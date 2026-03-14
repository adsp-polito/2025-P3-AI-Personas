"""Response synthesizer unit tests."""

import csv
from concurrent.futures import ThreadPoolExecutor as StdThreadPoolExecutor
import json
from pathlib import Path
import time

import pytest

import adsp.core.survey.response_synthesizer as response_synthesizer_module
from adsp.core.survey import (
    GroupGenerator,
    Question,
    RespondentProfile,
    ResponseSynthesizer,
    Survey,
    SurveyManager,
)
from adsp.core.survey.prompts import render_response_generation_prompt
from adsp.core.survey.utils import save_json, utc_now


def _write_traits(path: Path) -> None:
    payload = {
        "persona_id": "test-persona",
        "persona_name": "Test Persona",
        "summary_bio": "Synthetic profile used in tests",
        "key_indicators": [
            {
                "indicator_id": "behaviour",
                "indicator_category": "Behaviors",
                "statement_label": "Coffee Frequency",
                "statement_description": "Daily",
                "salience": {"is_salient": True, "magnitude": "strong"},
                "metrics": [],
            }
        ],
        "style_profile": {
            "tone_adjectives": ["friendly", "curious", "knowledgeable"],
            "formality_level": "medium",
            "directness": "balanced",
            "emotional_flavour": "enthusiastic",
            "criticality_level": "medium",
            "verbosity_preference": "balanced",
        },
        "value_frame": {
            "priority_rank": ["quality", "sustainability", "price"],
            "sustainability_orientation": "high",
            "price_sensitivity": "medium",
            "novelty_seeking": "high",
            "brand_loyalty": "medium",
            "health_concern": "medium",
        },
        "reasoning_policies": {
            "purchase_advice": {
                "default_biases": ["quality first"],
                "tradeoff_rules": ["quality over price"],
            },
            "product_evaluation": {
                "praise_triggers": ["taste"],
                "criticism_triggers": ["low quality"],
            },
        },
        "content_filters": {
            "avoid_styles": ["aggressive marketing"],
            "emphasise_disclaimers_on": ["health claims"],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_synthesizer_fixture(tmp_path: Path, *, respondent_count: int) -> tuple[ResponseSynthesizer, Survey, str]:
    base_dir = tmp_path / "surveys"
    traits_dir = tmp_path / "traits"
    traits_dir.mkdir(parents=True, exist_ok=True)
    _write_traits(traits_dir / "test-persona.json")

    surveys = SurveyManager(base_dir=base_dir)
    groups = GroupGenerator(base_dir=base_dir, traits_dirs=[traits_dir])
    synthesizer = ResponseSynthesizer(base_dir=base_dir)
    synthesizer.groups = groups

    survey = surveys.create_survey(
        {
            "title": "Parallel Simulation",
            "description": "Thread-pool sizing test",
            "questions": [
                {
                    "question_id": "q1",
                    "text": "Pick one",
                    "type": "multiple_choice",
                    "options": ["A", "B"],
                }
            ],
        }
    )
    group = groups.create_group(
        composition=[{"persona_id": "test-persona", "count": respondent_count}],
        mode="random",
        seed=33,
    )
    return synthesizer, survey, group.group_id


def test_run_simulation_and_export(tmp_path: Path):
    base_dir = tmp_path / "surveys"
    traits_dir = tmp_path / "traits"
    traits_dir.mkdir(parents=True, exist_ok=True)
    _write_traits(traits_dir / "test-persona.json")

    surveys = SurveyManager(base_dir=base_dir)
    groups = GroupGenerator(base_dir=base_dir, traits_dirs=[traits_dir])
    synthesizer = ResponseSynthesizer(base_dir=base_dir)
    synthesizer.groups = groups

    survey = surveys.create_survey(
        {
            "title": "Coffee Feedback",
            "description": "Test simulation",
            "questions": [
                {
                    "question_id": "q1",
                    "text": "Which option do you prefer?",
                    "type": "multiple_choice",
                    "options": ["Quality", "Price", "Brand"],
                },
                {
                    "question_id": "q2",
                    "text": "Share your coffee preference.",
                    "type": "open_ended",
                },
                {
                    "question_id": "q3",
                    "text": "Rate your interest in innovation.",
                    "type": "rating",
                    "metadata": {"scale": "1-5"},
                },
            ],
        }
    )
    group = groups.create_group(
        composition=[{"persona_id": "test-persona", "count": 2}],
        mode="random",
        seed=11,
    )

    result = synthesizer.run_simulation(survey_id=survey.survey_id, group_id=group.group_id)

    assert result.status == "completed"
    assert result.total_respondents == 2
    assert result.completed == 2

    responses = synthesizer.get_responses(survey_id=survey.survey_id, simulation_id=result.simulation_id)
    assert len(responses) == 2
    assert len(responses[0].answers) == 3

    details = synthesizer.get_response_details(
        survey_id=survey.survey_id,
        simulation_id=result.simulation_id,
    )
    assert details["survey_id"] == survey.survey_id
    assert details["simulation_id"] == result.simulation_id
    assert details["group_id"] == group.group_id
    assert details["total_responses"] == 2
    assert details["responses"][0]["persona_id"] == "test-persona"
    assert details["responses"][0]["answers"][0]["question_text"] == "Which option do you prefer?"

    csv_path = synthesizer.export_responses(
        survey_id=survey.survey_id,
        simulation_id=result.simulation_id,
        format="csv",
    )
    assert Path(csv_path).exists()
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert rows[0]["persona_id"] == "test-persona"
    assert rows[0]["question_text"] == "Which option do you prefer?"

    json_path = synthesizer.export_responses(
        survey_id=survey.survey_id,
        simulation_id=result.simulation_id,
        format="json",
    )
    assert Path(json_path).exists()
    export_payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    assert export_payload["responses"][0]["persona_id"] == "test-persona"
    assert export_payload["responses"][0]["answers"][0]["question_text"] == "Which option do you prefer?"

    stats = synthesizer.compute_response_statistics(
        survey_id=survey.survey_id,
        simulation_id=result.simulation_id,
    )
    assert stats["survey_id"] == survey.survey_id
    assert stats["simulation_id"] == result.simulation_id
    assert stats["total_respondents"] == 2
    assert stats["total_responses"] == 2
    assert len(stats["questions"]) == 3
    by_question = {item["question_id"]: item for item in stats["questions"]}
    assert by_question["q1"]["choice_distribution"]
    assert by_question["q3"]["rating_average"] is not None
    assert by_question["q2"]["text_response_count"] == 2
    assert synthesizer.has_statistics_cache(survey.survey_id, result.simulation_id)

    cached = synthesizer.compute_response_statistics(
        survey_id=survey.survey_id,
        simulation_id=result.simulation_id,
    )
    assert cached["computed_at"] == stats["computed_at"]


def test_background_simulation_updates_status_until_completed(tmp_path: Path):
    base_dir = tmp_path / "surveys"
    traits_dir = tmp_path / "traits"
    traits_dir.mkdir(parents=True, exist_ok=True)
    _write_traits(traits_dir / "test-persona.json")

    surveys = SurveyManager(base_dir=base_dir)
    groups = GroupGenerator(base_dir=base_dir, traits_dirs=[traits_dir])
    synthesizer = ResponseSynthesizer(base_dir=base_dir)
    synthesizer.groups = groups

    survey = surveys.create_survey(
        {
            "title": "Background Simulation",
            "description": "Async status test",
            "questions": [
                {
                    "question_id": "q1",
                    "text": "Pick one",
                    "type": "multiple_choice",
                    "options": ["A", "B"],
                }
            ],
        }
    )
    group = groups.create_group(
        composition=[{"persona_id": "test-persona", "count": 6}],
        mode="random",
        seed=22,
    )

    initial = synthesizer.run_simulation_background(
        survey_id=survey.survey_id,
        group_id=group.group_id,
    )
    assert initial.status == "processing"

    timeout_at = time.time() + 15
    latest = initial
    while time.time() < timeout_at:
        latest = synthesizer.get_simulation_result(survey.survey_id, initial.simulation_id)
        if latest.status != "processing":
            break
        time.sleep(0.05)

    assert latest.status == "completed"
    assert latest.pending == 0
    assert latest.completed == latest.total_respondents


def test_statistics_require_completed_simulation(tmp_path: Path):
    base_dir = tmp_path / "surveys"
    surveys = SurveyManager(base_dir=base_dir)
    synthesizer = ResponseSynthesizer(base_dir=base_dir)

    survey = surveys.create_survey(
        {
            "survey_id": "survey-processing-only",
            "title": "Processing State",
            "description": "",
            "questions": [
                {
                    "question_id": "q1",
                    "text": "Pick one",
                    "type": "multiple_choice",
                    "options": ["Yes", "No"],
                }
            ],
        }
    )

    simulation_id = "sim-processing"
    save_json(
        synthesizer.responses_dir / survey.survey_id / simulation_id / "simulation.json",
        {
            "simulation_id": simulation_id,
            "survey_id": survey.survey_id,
            "group_id": "group-x",
            "status": "processing",
            "started_at": utc_now().isoformat(),
            "completed_at": None,
            "total_respondents": 1,
            "completed": 0,
            "pending": 1,
            "response_ids": [],
        },
    )

    with pytest.raises(RuntimeError):
        synthesizer.compute_response_statistics(
            survey_id=survey.survey_id,
            simulation_id=simulation_id,
        )


def test_llm_prompt_uses_profile_description_instead_of_respondent_json(tmp_path: Path):
    respondent = RespondentProfile(
        respondent_id="resp-001",
        persona_id="curious-connoisseurs",
        name="Ari Test",
        key_indicators=[
            {
                "statement_label": "Flavor Discovery",
                "statement_description": "Looks for nuanced notes in each blend.",
            }
        ],
        style_profile={
            "tone_adjectives": ["curious", "analytical"],
            "formality_level": "medium",
            "verbosity_preference": "balanced",
        },
        value_frame={
            "priority_rank": ["quality", "sustainability", "price"],
            "novelty_seeking": "high",
        },
        reasoning_policies={
            "purchase_advice": {
                "default_biases": ["quality first"],
                "tradeoff_rules": ["quality over price"],
            }
        },
        content_filters={"avoid_styles": ["aggressive marketing"]},
    )
    survey = Survey(
        survey_id="survey-001",
        title="Coffee Survey",
        description="Prompt rendering test",
        questions=[
            Question(
                question_id="q1",
                text="Which factor matters most?",
                type="multiple_choice",
                options=["Taste", "Price", "Sustainability"],
            )
        ],
    )

    prompt = render_response_generation_prompt(survey=survey, respondent=respondent)

    assert "Respondent persona:" in prompt
    assert "Persona segment: curious-connoisseurs" in prompt
    assert "Communication style:" in prompt
    assert "Decision framing:" in prompt
    assert "Respondent:\n{" not in prompt


def test_run_simulation_uses_default_parallel_workers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.delenv("ADSP_SURVEY_SIMULATION_MAX_WORKERS", raising=False)
    synthesizer, survey, group_id = _make_synthesizer_fixture(tmp_path, respondent_count=6)
    captured: dict[str, int | None] = {"max_workers": None}

    class SpyThreadPoolExecutor(StdThreadPoolExecutor):
        def __init__(self, max_workers=None, *args, **kwargs):
            captured["max_workers"] = max_workers
            super().__init__(max_workers=max_workers, *args, **kwargs)

    monkeypatch.setattr(response_synthesizer_module, "ThreadPoolExecutor", SpyThreadPoolExecutor)

    result = synthesizer.run_simulation(survey_id=survey.survey_id, group_id=group_id)

    assert result.status == "completed"
    assert captured["max_workers"] == 4


def test_run_simulation_uses_configured_parallel_workers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ADSP_SURVEY_SIMULATION_MAX_WORKERS", "2")
    synthesizer, survey, group_id = _make_synthesizer_fixture(tmp_path, respondent_count=6)
    captured: dict[str, int | None] = {"max_workers": None}

    class SpyThreadPoolExecutor(StdThreadPoolExecutor):
        def __init__(self, max_workers=None, *args, **kwargs):
            captured["max_workers"] = max_workers
            super().__init__(max_workers=max_workers, *args, **kwargs)

    monkeypatch.setattr(response_synthesizer_module, "ThreadPoolExecutor", SpyThreadPoolExecutor)

    result = synthesizer.run_simulation(survey_id=survey.survey_id, group_id=group_id)

    assert result.status == "completed"
    assert captured["max_workers"] == 2
