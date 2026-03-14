"""Survey response generation for simulated respondents."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import timezone
import os
from pathlib import Path
import random
import threading
from typing import Any, Dict, Iterator, List, Mapping, Sequence, Tuple

from loguru import logger

from adsp.config import PROCESSED_DATA_DIR
from adsp.utils.progress import progress_bar

from .group_generator import GroupGenerator
from .models import (
    Answer,
    RespondentGroup,
    RespondentProfile,
    SimulationResult,
    Survey,
    SurveyResponse,
)
from .prompts import RESPONSE_SYSTEM_PROMPT, render_response_generation_prompt
from .survey_manager import SurveyManager
from .utils import (
    ensure_dir,
    load_json,
    make_identifier,
    model_dump,
    parse_json_block,
    save_json,
    utc_now,
)
from .validators import validate_simulation_result, validate_survey_response


class ResponseSynthesizer:
    """Generates survey responses and persists simulation results."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir or (PROCESSED_DATA_DIR / "surveys"))
        self.responses_dir = ensure_dir(self.base_dir / "responses")
        self.surveys = SurveyManager(base_dir=self.base_dir)
        self.groups = GroupGenerator(base_dir=self.base_dir)

    def generate_responses(
        self,
        survey_id: str,
        group_id: str,
    ) -> Iterator[SurveyResponse]:
        simulation = self.run_simulation(survey_id=survey_id, group_id=group_id)
        responses = self.get_responses(survey_id=survey_id, simulation_id=simulation.simulation_id)
        for response in responses:
            yield response
    def _start_simulation(
        self,
        *,
        survey_id: str,
        group_id: str,
    ) -> Tuple[Survey, RespondentGroup, str, SimulationResult]:
        survey = self.surveys.get_survey(survey_id)
        group = self.groups.get_group(group_id)
        simulation_id = make_identifier("sim")
        processing = self._init_processing_result(
            survey_id=survey_id,
            group_id=group_id,
            total_respondents=len(group.respondents),
            simulation_id=simulation_id,
        )
        self._persist_simulation_state(survey_id=survey_id, simulation_id=simulation_id, result=processing)
        return survey, group, simulation_id, processing

    def run_simulation(
        self,
        *,
        survey_id: str,
        group_id: str,
    ) -> SimulationResult:
        survey, group, simulation_id, processing = self._start_simulation(survey_id=survey_id, group_id=group_id)
        logger.info(
            "Starting survey simulation survey={} group={} simulation={} total_respondents={}",
            survey_id,
            group_id,
            simulation_id,
            len(group.respondents),
        )
        self._persist_simulation_state(survey_id=survey_id, simulation_id=simulation_id, result=processing)
        return self._execute_simulation(survey=survey, group=group, simulation_id=simulation_id, started_at=processing.started_at)

    def run_simulation_background(
        self,
        *,
        survey_id: str,
        group_id: str,
    ) -> SimulationResult:
        survey, group, simulation_id, processing = self._start_simulation(survey_id=survey_id, group_id=group_id)
        logger.info(
            "Queued background survey simulation survey={} group={} simulation={} total_respondents={}",
            survey_id,
            group_id,
            simulation_id,
            len(group.respondents),
        )

        worker = threading.Thread(
            target=self._run_simulation_worker,
            kwargs={
                "survey": survey,
                "group": group,
                "simulation_id": simulation_id,
                "started_at": processing.started_at,
            },
            name=f"survey-sim-{simulation_id}",
            daemon=True,
        )
        worker.start()
        return processing

    def _init_processing_result(
        self,
        *,
        survey_id: str,
        group_id: str,
        total_respondents: int,
        simulation_id: str,
    ) -> SimulationResult:
        return SimulationResult(
            simulation_id=simulation_id,
            survey_id=survey_id,
            group_id=group_id,
            status="processing",
            started_at=utc_now(),
            completed_at=None,
            total_respondents=total_respondents,
            completed=0,
            pending=total_respondents,
            response_ids=[],
        )

    def _run_simulation_worker(
        self,
        *,
        survey: Survey,
        group: RespondentGroup,
        simulation_id: str,
        started_at: Any,
    ) -> None:
        try:
            self._execute_simulation(
                survey=survey,
                group=group,
                simulation_id=simulation_id,
                started_at=started_at,
            )
        except Exception as exc:
            logger.exception(
                "Background simulation failed survey={} simulation={} error={}",
                survey.survey_id,
                simulation_id,
                exc,
            )

    def _execute_simulation(
        self,
        *,
        survey: Survey,
        group: RespondentGroup,
        simulation_id: str,
        started_at: Any,
    ) -> SimulationResult:
        total = len(group.respondents)
        responses_by_index: List[SurveyResponse | None] = [None] * total
        responses: List[SurveyResponse] = []
        max_workers = self._simulation_max_workers(total_respondents=total)

        logger.info(
            "Running survey simulation survey={} group={} simulation={} workers={} total_respondents={}",
            survey.survey_id,
            group.group_id,
            simulation_id,
            max_workers,
            total,
        )

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor, progress_bar(
                total=total,
                desc=f"Survey simulation {simulation_id}",
                unit="resp",
                leave=False,
            ) as bar:
                futures = {
                    executor.submit(self.generate_single_response, survey=survey, respondent=respondent): index
                    for index, respondent in enumerate(group.respondents)
                }
                for future in as_completed(futures):
                    index = futures[future]
                    response = future.result()
                    responses_by_index[index] = response
                    responses = [item for item in responses_by_index if item is not None]
                    progress = SimulationResult(
                        simulation_id=simulation_id,
                        survey_id=survey.survey_id,
                        group_id=group.group_id,
                        status="processing",
                        started_at=started_at,
                        completed_at=None,
                        total_respondents=total,
                        completed=len(responses),
                        pending=max(0, total - len(responses)),
                        response_ids=[response.response_id for response in responses],
                    )
                    self._persist_simulation_state(
                        survey_id=survey.survey_id,
                        simulation_id=simulation_id,
                        result=progress,
                    )
                    completed_count = len(responses)
                    pending_count = max(0, total - completed_count)
                    bar.update(1)
                    bar.set_postfix(completed=completed_count, pending=pending_count, refresh=False)
        except Exception:
            responses = [item for item in responses_by_index if item is not None]
            failed = SimulationResult(
                simulation_id=simulation_id,
                survey_id=survey.survey_id,
                group_id=group.group_id,
                status="failed",
                started_at=started_at,
                completed_at=utc_now(),
                total_respondents=total,
                completed=len(responses),
                pending=max(0, total - len(responses)),
                response_ids=[response.response_id for response in responses],
            )
            self._persist_simulation(
                survey_id=survey.survey_id,
                simulation_id=simulation_id,
                result=failed,
                responses=responses,
            )
            logger.error(
                "Survey simulation failed survey={} simulation={} completed={}/{}",
                survey.survey_id,
                simulation_id,
                len(responses),
                total,
            )
            raise

        responses = [item for item in responses_by_index if item is not None]
        completed = SimulationResult(
            simulation_id=simulation_id,
            survey_id=survey.survey_id,
            group_id=group.group_id,
            status="completed",
            started_at=started_at,
            completed_at=utc_now(),
            total_respondents=total,
            completed=len(responses),
            pending=max(0, total - len(responses)),
            response_ids=[response.response_id for response in responses],
        )
        self._persist_simulation(
            survey_id=survey.survey_id,
            simulation_id=simulation_id,
            result=completed,
            responses=responses,
        )
        logger.info(
            "Survey simulation completed survey={} simulation={} completed={}/{}",
            survey.survey_id,
            simulation_id,
            len(responses),
            total,
        )
        return completed

    def generate_single_response(
        self,
        survey_id: str | None = None,
        respondent: RespondentProfile | Mapping[str, Any] | None = None,
        *,
        survey: Survey | None = None,
    ) -> SurveyResponse:
        if survey is None:
            if survey_id is None:
                raise ValueError("survey_id is required when survey is not provided")
            survey = self.surveys.get_survey(survey_id)
        if respondent is None:
            raise ValueError("respondent is required")

        profile = respondent if isinstance(respondent, RespondentProfile) else RespondentProfile(**dict(respondent))
        answers = self._generate_answers_for_profile(survey=survey, respondent=profile)

        payload = {
            "response_id": make_identifier("resp"),
            "survey_id": survey.survey_id,
            "respondent_id": profile.respondent_id,
            "completed_at": utc_now(),
            "answers": [model_dump(answer) for answer in answers],
        }
        return validate_survey_response(payload)

    def export_responses(
        self,
        survey_id: str,
        format: str = "csv",
        *,
        simulation_id: str | None = None,
        output_path: str | Path | None = None,
    ) -> str:
        chosen_simulation = simulation_id or self._latest_simulation_id(survey_id)
        simulation_dir = self.responses_dir / survey_id / chosen_simulation
        if not simulation_dir.exists():
            raise KeyError(f"Simulation '{chosen_simulation}' not found for survey '{survey_id}'")

        format_normalized = (format or "csv").strip().lower()
        if format_normalized not in {"csv", "json"}:
            raise ValueError("format must be either 'csv' or 'json'")

        details = self.get_response_details(survey_id, simulation_id=chosen_simulation)
        source = simulation_dir / f"responses_export.{format_normalized}"
        if format_normalized == "json":
            save_json(source, details)
        else:
            self._write_export_csv(source, details)

        if output_path is None:
            return str(source)

        destination = Path(output_path)
        ensure_dir(destination.parent)
        destination.write_bytes(source.read_bytes())
        return str(destination)

    def get_simulation_result(self, survey_id: str, simulation_id: str) -> SimulationResult:
        path = self.responses_dir / survey_id / simulation_id / "simulation.json"
        if not path.exists():
            raise KeyError(f"Simulation '{simulation_id}' not found for survey '{survey_id}'")
        payload = load_json(path)
        return validate_simulation_result(payload)

    def list_simulations(self, survey_id: str) -> List[SimulationResult]:
        survey_dir = self.responses_dir / survey_id
        if not survey_dir.exists():
            return []

        items: List[SimulationResult] = []
        for path in sorted(survey_dir.glob("*/simulation.json")):
            try:
                items.append(validate_simulation_result(load_json(path)))
            except Exception as exc:
                logger.warning("Skipping invalid simulation metadata {}: {}", path, exc)
        return items

    def get_responses(self, survey_id: str, simulation_id: str) -> List[SurveyResponse]:
        path = self.responses_dir / survey_id / simulation_id / "responses.json"
        if not path.exists():
            raise KeyError(f"Response file not found for simulation '{simulation_id}'")

        payload = load_json(path)
        if not isinstance(payload, list):
            raise ValueError("responses.json payload must be a list")

        responses: List[SurveyResponse] = []
        for item in payload:
            responses.append(validate_survey_response(item))
        return responses

    def get_response_details(
        self,
        survey_id: str,
        *,
        simulation_id: str | None = None,
    ) -> Dict[str, Any]:
        chosen_simulation = simulation_id or self._latest_simulation_id(survey_id)
        survey = self.surveys.get_survey(survey_id)
        simulation = self.get_simulation_result(survey_id, chosen_simulation)
        if simulation.status != "completed":
            raise RuntimeError(f"Simulation '{chosen_simulation}' is not completed yet")

        group = self.groups.get_group(simulation.group_id)
        responses = self.get_responses(survey_id, chosen_simulation)

        question_by_id = {question.question_id: question for question in survey.questions}
        respondent_by_id = {respondent.respondent_id: respondent for respondent in group.respondents}

        items: List[Dict[str, Any]] = []
        for response in responses:
            respondent = respondent_by_id.get(response.respondent_id)
            answers_payload: List[Dict[str, Any]] = []
            for answer in response.answers:
                question = question_by_id.get(answer.question_id)
                answers_payload.append(
                    {
                        "question_id": answer.question_id,
                        "question_text": question.text if question is not None else answer.question_id,
                        "answer_type": answer.answer_type,
                        "value": answer.value,
                        "confidence": answer.confidence,
                        "reasoning": answer.reasoning,
                    }
                )

            items.append(
                {
                    "response_id": response.response_id,
                    "respondent_id": response.respondent_id,
                    "respondent_name": respondent.name if respondent is not None else None,
                    "persona_id": respondent.persona_id if respondent is not None else None,
                    "completed_at": response.completed_at.astimezone(timezone.utc).isoformat(),
                    "answers": answers_payload,
                }
            )

        return {
            "survey_id": survey.survey_id,
            "simulation_id": chosen_simulation,
            "group_id": simulation.group_id,
            "total_responses": len(items),
            "responses": items,
        }

    def statistics_cache_path(self, survey_id: str, simulation_id: str) -> Path:
        return self.responses_dir / survey_id / simulation_id / "statistics.json"

    def has_statistics_cache(self, survey_id: str, simulation_id: str) -> bool:
        return self.statistics_cache_path(survey_id, simulation_id).exists()

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None
            try:
                return float(raw)
            except ValueError:
                return None
        return None

    @staticmethod
    def _env_positive_int(name: str, default: int) -> int:
        raw = os.environ.get(name)
        if raw is None or not raw.strip():
            return default
        try:
            parsed = int(raw)
        except ValueError:
            logger.warning("{} must be an integer >= 1; falling back to {}", name, default)
            return default
        if parsed < 1:
            logger.warning("{} must be an integer >= 1; falling back to {}", name, default)
            return default
        return parsed

    def _simulation_max_workers(self, *, total_respondents: int) -> int:
        configured = self._env_positive_int("ADSP_SURVEY_SIMULATION_MAX_WORKERS", 4)
        if total_respondents <= 0:
            return 1
        return min(configured, total_respondents)

    def compute_response_statistics(
        self,
        *,
        survey_id: str,
        simulation_id: str | None = None,
    ) -> Dict[str, Any]:
        chosen_simulation = simulation_id or self._latest_simulation_id(survey_id)
        simulation = self.get_simulation_result(survey_id=survey_id, simulation_id=chosen_simulation)
        if simulation.status != "completed":
            raise RuntimeError(
                f"Simulation '{chosen_simulation}' for survey '{survey_id}' is not completed (status={simulation.status})"
            )

        stats_path = self.statistics_cache_path(survey_id, chosen_simulation)
        if stats_path.exists():
            payload = load_json(stats_path)
            if isinstance(payload, Mapping):
                return dict(payload)

        survey = self.surveys.get_survey(survey_id)
        responses = self.get_responses(survey_id=survey_id, simulation_id=chosen_simulation)

        answers_by_question: Dict[str, List[Answer]] = {question.question_id: [] for question in survey.questions}
        for response in responses:
            for answer in response.answers:
                bucket = answers_by_question.get(answer.question_id)
                if bucket is not None:
                    bucket.append(answer)

        question_stats: List[Dict[str, Any]] = []
        total_respondents = simulation.total_respondents or len(responses)
        for question in survey.questions:
            answers = answers_by_question.get(question.question_id, [])
            answered_values = [answer for answer in answers if answer.value not in (None, "")]
            answered_count = len(answered_values)
            response_rate = round((answered_count / total_respondents), 4) if total_respondents else 0.0

            payload: Dict[str, Any] = {
                "question_id": question.question_id,
                "text": question.text,
                "type": question.type,
                "answered_count": answered_count,
                "response_rate": response_rate,
                "choice_distribution": [],
                "rating_distribution": [],
                "rating_average": None,
                "rating_min": None,
                "rating_max": None,
                "text_response_count": 0,
                "sample_text_responses": [],
            }

            if question.type == "multiple_choice":
                choices = [str(answer.value).strip() for answer in answered_values if str(answer.value).strip()]
                counts = Counter(choices)
                total_choice_answers = sum(counts.values())
                distribution: List[Dict[str, Any]] = []
                seen: set[str] = set()

                for option in question.options:
                    option_value = str(option)
                    count = counts.get(option_value, 0)
                    distribution.append(
                        {
                            "value": option_value,
                            "count": count,
                            "percentage": round((count / total_choice_answers), 4) if total_choice_answers else 0.0,
                        }
                    )
                    seen.add(option_value)

                for value in sorted(choice for choice in counts if choice not in seen):
                    count = counts[value]
                    distribution.append(
                        {
                            "value": value,
                            "count": count,
                            "percentage": round((count / total_choice_answers), 4) if total_choice_answers else 0.0,
                        }
                    )

                payload["choice_distribution"] = distribution

            elif question.type == "rating":
                ratings = [
                    rating
                    for rating in (self._coerce_float(answer.value) for answer in answered_values)
                    if rating is not None
                ]
                if ratings:
                    payload["rating_average"] = round(sum(ratings) / len(ratings), 2)
                    payload["rating_min"] = min(ratings)
                    payload["rating_max"] = max(ratings)

                labels = [str(int(rating)) if float(rating).is_integer() else str(rating) for rating in ratings]
                counts = Counter(labels)
                total_ratings = sum(counts.values())

                def _rating_sort_key(raw: str) -> Tuple[int, float | str]:
                    parsed = self._coerce_float(raw)
                    if parsed is None:
                        return (1, raw)
                    return (0, parsed)

                payload["rating_distribution"] = [
                    {
                        "value": value,
                        "count": counts[value],
                        "percentage": round((counts[value] / total_ratings), 4) if total_ratings else 0.0,
                    }
                    for value in sorted(counts.keys(), key=_rating_sort_key)
                ]

            else:
                texts = [str(answer.value).strip() for answer in answered_values if str(answer.value).strip()]
                payload["text_response_count"] = len(texts)
                payload["sample_text_responses"] = texts[:3]

            question_stats.append(payload)

        payload = {
            "survey_id": survey_id,
            "simulation_id": chosen_simulation,
            "total_respondents": total_respondents,
            "total_responses": len(responses),
            "computed_at": utc_now().isoformat(),
            "questions": question_stats,
        }
        save_json(stats_path, payload)
        return payload

    def _generate_answers_for_profile(self, *, survey: Survey, respondent: RespondentProfile) -> List[Answer]:
        generated = self._generate_answers_with_llm(survey=survey, respondent=respondent)
        if generated is not None:
            return generated

        answers: List[Answer] = []
        for question in survey.questions:
            answers.append(self._generate_answer_rule_based(question=question, respondent=respondent))
        return answers

    def _generate_answer_rule_based(self, *, question: Any, respondent: RespondentProfile) -> Answer:
        seed = hash((respondent.respondent_id, question.question_id, respondent.seed)) & 0xFFFFFFFF
        rng = random.Random(seed)

        if question.type == "multiple_choice":
            choice, confidence, reasoning = self._pick_multiple_choice_answer(question=question, respondent=respondent, rng=rng)
            return Answer(
                question_id=question.question_id,
                answer_type="choice",
                value=choice,
                confidence=confidence,
                reasoning=reasoning,
            )

        if question.type == "rating":
            rating, confidence, reasoning = self._pick_rating_answer(question=question, respondent=respondent, rng=rng)
            return Answer(
                question_id=question.question_id,
                answer_type="rating",
                value=rating,
                confidence=confidence,
                reasoning=reasoning,
            )

        text, confidence, reasoning = self._compose_open_ended_answer(question=question, respondent=respondent)
        return Answer(
            question_id=question.question_id,
            answer_type="text",
            value=text,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _pick_multiple_choice_answer(
        self,
        *,
        question: Any,
        respondent: RespondentProfile,
        rng: random.Random,
    ) -> Tuple[str, float, str]:
        options = [str(option) for option in (question.options or [])]
        if not options:
            return "", 0.3, "No options provided"

        priorities = [str(item).lower() for item in respondent.value_frame.get("priority_rank", []) if item]
        preference_flags = {
            "sustainability": str(respondent.value_frame.get("sustainability_orientation", "")).lower(),
            "price": str(respondent.value_frame.get("price_sensitivity", "")).lower(),
            "novelty": str(respondent.value_frame.get("novelty_seeking", "")).lower(),
            "brand": str(respondent.value_frame.get("brand_loyalty", "")).lower(),
            "health": str(respondent.value_frame.get("health_concern", "")).lower(),
        }

        scored: List[Tuple[float, str]] = []
        for option in options:
            lower = option.lower()
            score = rng.uniform(0.0, 0.4)

            if "sustain" in lower and preference_flags["sustainability"] == "high":
                score += 1.5
            if any(token in lower for token in ("discount", "budget", "cheap", "price")) and preference_flags["price"] == "high":
                score += 1.5
            if any(token in lower for token in ("new", "innovative", "limited", "experiment")) and preference_flags["novelty"] == "high":
                score += 1.5
            if any(token in lower for token in ("brand", "trusted", "familiar")) and preference_flags["brand"] == "high":
                score += 1.0
            if any(token in lower for token in ("healthy", "low sugar", "wellness")) and preference_flags["health"] == "high":
                score += 1.0

            for priority in priorities[:3]:
                if priority and priority in lower:
                    score += 0.6

            scored.append((score, option))

        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[0][1]
        confidence = min(0.95, max(0.55, 0.65 + scored[0][0] * 0.08))
        reasoning = "Selected option that best matches value priorities"
        return best, round(confidence, 2), reasoning

    def _pick_rating_answer(
        self,
        *,
        question: Any,
        respondent: RespondentProfile,
        rng: random.Random,
    ) -> Tuple[int, float, str]:
        min_scale, max_scale = self._parse_scale(question.metadata)
        midpoint = int(round((min_scale + max_scale) / 2))
        rating = midpoint

        novelty = str(respondent.value_frame.get("novelty_seeking", "")).lower()
        sustainability = str(respondent.value_frame.get("sustainability_orientation", "")).lower()
        price = str(respondent.value_frame.get("price_sensitivity", "")).lower()
        loyalty = str(respondent.value_frame.get("brand_loyalty", "")).lower()

        lower_q = question.text.lower()

        if novelty == "high":
            rating += 1
        if sustainability == "high" and "sustain" in lower_q:
            rating += 1
        if price == "high" and any(token in lower_q for token in ("premium", "expensive", "high price")):
            rating -= 1
        if loyalty == "high" and any(token in lower_q for token in ("brand", "loyal")):
            rating += 1

        rating += rng.choice([-1, 0, 0, 1])
        rating = max(min_scale, min(max_scale, rating))

        confidence = round(rng.uniform(0.55, 0.88), 2)
        reasoning = "Rating inferred from respondent priorities and question framing"
        return rating, confidence, reasoning

    def _compose_open_ended_answer(self, *, question: Any, respondent: RespondentProfile) -> Tuple[str, float, str]:
        priorities = [str(item) for item in respondent.value_frame.get("priority_rank", []) if item]
        tones = [str(item) for item in respondent.style_profile.get("tone_adjectives", []) if item]

        top_priorities = priorities[:2] if priorities else ["quality"]
        tone = tones[0] if tones else "pragmatic"

        indicator_hint = ""
        if respondent.key_indicators:
            first = respondent.key_indicators[0]
            if isinstance(first, dict):
                label = first.get("statement_label")
                description = first.get("statement_description")
                if label and description:
                    indicator_hint = f" {label}: {description}."

        sentence = (
            f"I usually prioritize {', '.join(top_priorities)} when I decide, "
            f"so for this I would focus on options that fit those values in a {tone} way."
            f"{indicator_hint}"
        ).strip()

        verbosity = str(respondent.style_profile.get("verbosity_preference", "balanced")).lower()
        if verbosity == "concise" and len(sentence) > 140:
            sentence = sentence[:137].rstrip() + "..."

        confidence = 0.68
        reasoning = f"Open-ended answer aligned with priorities: {', '.join(top_priorities)}"
        return sentence, confidence, reasoning

    @staticmethod
    def _parse_scale(metadata: Mapping[str, Any]) -> Tuple[int, int]:
        default = (1, 5)
        if not isinstance(metadata, Mapping):
            return default

        scale = metadata.get("scale")
        if isinstance(scale, str) and "-" in scale:
            left, right = scale.split("-", 1)
            try:
                minimum = int(left.strip())
                maximum = int(right.strip())
                if minimum < maximum:
                    return minimum, maximum
            except ValueError:
                return default

        if isinstance(scale, Sequence) and len(scale) == 2:
            try:
                minimum = int(scale[0])
                maximum = int(scale[1])
                if minimum < maximum:
                    return minimum, maximum
            except Exception:
                return default

        return default

    def _persist_simulation(
        self,
        *,
        survey_id: str,
        simulation_id: str,
        result: SimulationResult,
        responses: List[SurveyResponse],
    ) -> None:
        simulation_dir = ensure_dir(self.responses_dir / survey_id / simulation_id)

        responses_payload = [model_dump(response) for response in responses]
        save_json(simulation_dir / "responses.json", responses_payload)
        self._persist_simulation_state(survey_id=survey_id, simulation_id=simulation_id, result=result)
        self._write_csv(simulation_dir / "responses.csv", responses)

    def _persist_simulation_state(
        self,
        *,
        survey_id: str,
        simulation_id: str,
        result: SimulationResult,
    ) -> None:
        simulation_dir = ensure_dir(self.responses_dir / survey_id / simulation_id)
        save_json(simulation_dir / "simulation.json", model_dump(result))

    @staticmethod
    def _response_export_rows(details: Mapping[str, Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        survey_id = details.get("survey_id")
        simulation_id = details.get("simulation_id")
        group_id = details.get("group_id")

        responses = details.get("responses", [])
        if not isinstance(responses, list):
            return rows

        for response in responses:
            if not isinstance(response, Mapping):
                continue

            for answer in response.get("answers", []):
                if not isinstance(answer, Mapping):
                    continue
                rows.append(
                    {
                        "response_id": response.get("response_id"),
                        "survey_id": survey_id,
                        "simulation_id": simulation_id,
                        "group_id": group_id,
                        "respondent_id": response.get("respondent_id"),
                        "respondent_name": response.get("respondent_name"),
                        "persona_id": response.get("persona_id"),
                        "completed_at": response.get("completed_at"),
                        "question_id": answer.get("question_id"),
                        "question_text": answer.get("question_text"),
                        "answer_type": answer.get("answer_type"),
                        "value": answer.get("value"),
                        "confidence": answer.get("confidence"),
                        "reasoning": answer.get("reasoning") or "",
                    }
                )

        return rows

    def _write_export_csv(self, path: Path, details: Mapping[str, Any]) -> None:
        ensure_dir(path.parent)
        rows = self._response_export_rows(details)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "response_id",
                    "survey_id",
                    "simulation_id",
                    "group_id",
                    "respondent_id",
                    "respondent_name",
                    "persona_id",
                    "completed_at",
                    "question_id",
                    "question_text",
                    "answer_type",
                    "value",
                    "confidence",
                    "reasoning",
                ],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _write_csv(self, path: Path, responses: List[SurveyResponse]) -> None:
        ensure_dir(path.parent)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "response_id",
                    "survey_id",
                    "respondent_id",
                    "completed_at",
                    "question_id",
                    "answer_type",
                    "value",
                    "confidence",
                    "reasoning",
                ],
            )
            writer.writeheader()
            for response in responses:
                for answer in response.answers:
                    writer.writerow(
                        {
                            "response_id": response.response_id,
                            "survey_id": response.survey_id,
                            "respondent_id": response.respondent_id,
                            "completed_at": response.completed_at.astimezone(timezone.utc).isoformat(),
                            "question_id": answer.question_id,
                            "answer_type": answer.answer_type,
                            "value": answer.value,
                            "confidence": answer.confidence,
                            "reasoning": answer.reasoning or "",
                        }
                    )

    def _latest_simulation_id(self, survey_id: str) -> str:
        survey_dir = self.responses_dir / survey_id
        if not survey_dir.exists():
            raise KeyError(f"No simulations found for survey '{survey_id}'")

        candidates = [path for path in survey_dir.iterdir() if path.is_dir()]
        if not candidates:
            raise KeyError(f"No simulations found for survey '{survey_id}'")

        latest = max(candidates, key=lambda path: path.stat().st_mtime)
        return latest.name

    def _generate_answers_with_llm(
        self,
        *,
        survey: Survey,
        respondent: RespondentProfile,
    ) -> List[Answer] | None:
        backend = os.environ.get("ADSP_LLM_BACKEND", "stub").strip().lower()
        if backend != "openai":
            return None

        base_url = os.environ.get("ADSP_LLM_BASE_URL") or os.environ.get("VLLM_BASE_URL")
        model = os.environ.get("ADSP_LLM_MODEL") or os.environ.get("VLLM_MODEL")
        api_key = os.environ.get("ADSP_LLM_API_KEY") or os.environ.get("VLLM_API_KEY", "EMPTY")
        if not model:
            return None

        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return None

        client = OpenAI(base_url=base_url, api_key=api_key)
        prompt = render_response_generation_prompt(survey=survey, respondent=respondent)

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=float(os.environ.get("ADSP_SURVEY_LLM_TEMPERATURE", "0.2")),
                max_tokens=int(os.environ.get("ADSP_SURVEY_LLM_MAX_TOKENS", "1200")),
                timeout=float(os.environ.get("ADSP_SURVEY_LLM_TIMEOUT", "60")),
            )
        except Exception as exc:
            logger.warning("LLM response generation failed for respondent {}: {}", respondent.respondent_id, exc)
            return None

        content = completion.choices[0].message.content if completion.choices else ""
        parsed = parse_json_block(content or "")
        if not isinstance(parsed, dict):
            return None

        raw_answers = parsed.get("answers")
        if not isinstance(raw_answers, list):
            return None

        by_question = {question.question_id: question for question in survey.questions}
        answers: List[Answer] = []
        for item in raw_answers:
            if not isinstance(item, dict):
                continue
            question_id = item.get("question_id")
            if not isinstance(question_id, str) or question_id not in by_question:
                continue
            question = by_question[question_id]

            if question.type == "multiple_choice":
                answer_type = "choice"
            elif question.type == "rating":
                answer_type = "rating"
            else:
                answer_type = "text"

            answers.append(
                Answer(
                    question_id=question_id,
                    answer_type=answer_type,
                    value=item.get("value"),
                    confidence=0.7,
                    reasoning=item.get("reasoning") if isinstance(item.get("reasoning"), str) else None,
                )
            )

        if len(answers) != len(survey.questions):
            return None
        return answers
