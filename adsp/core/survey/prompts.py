"""Prompt templates for survey simulation."""

from __future__ import annotations

import json
import random
from typing import Any, List, Mapping, Sequence

from .models import RespondentProfile, Survey

RESPONSE_SYSTEM_PROMPT = (
    "You answer survey questions as the provided persona profile. "
    "Return strict JSON only, no markdown and no extra text."
)

SURVEY_SIMULATION_PRIMING_PROMPT = """
You are given a survey and a respondent profile. Answer the survey as if you are this respondent.

Instructions:
- Use the respondent profile as persona guidance for all answers.
- Answer every question. Do not omit any question.
- Keep responses consistent with the respondent’s preferences, priorities, communication style, and reasoning guidance.
- For each answer, include:
  - "question_id": the exact question ID
  - "value": the selected answer or rating
  - "reasoning": a brief but specific explanation grounded in the profile

Output format:
Return valid JSON only, with this exact structure:
{"answers":[{"question_id":"...","value":"...","reasoning":"..."}]}

Rules:
- Do not include any text outside the JSON.
- For multiple-choice questions, the "value" must exactly match one of the provided options.
- For rating questions, the "value" must be a valid value within the specified scale.
- Base all reasoning on the profile and persona, not on generic assumptions.
- Ensure the reasoning reflects likely tradeoffs, such as sustainability over convenience, innovation over brand loyalty, and quality over price when relevant.

"""


def _coerce_str_list(value: Any) -> List[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _describe_respondent_for_prompt(respondent: RespondentProfile) -> str:
    lines = [
        f"Respondent id: {respondent.respondent_id}",
        f"Persona segment: {respondent.persona_id}",
        f"Name: {respondent.name}",
        f"Country: {respondent.country}",
        f"Gender: {respondent.gender}",
        f"Ethnicity: {respondent.ethnicity}",
    ]

    style = respondent.style_profile if isinstance(respondent.style_profile, Mapping) else {}
    tones = _coerce_str_list(style.get("tone_adjectives"))
    style_parts: List[str] = []
    if tones:
        style_parts.append(f"tone adjectives: {', '.join(tones[:5])}")
    for key, label in (
            ("formality_level", "formality"),
            ("directness", "directness"),
            ("emotional_flavour", "emotional flavour"),
            ("criticality_level", "criticality level"),
            ("verbosity_preference", "verbosity"),
    ):
        value = style.get(key)
        if isinstance(value, str) and value.strip():
            style_parts.append(f"{label}: {value.strip()}")
    if style_parts:
        lines.append(f"Communication style: {'; '.join(style_parts)}")

    value_frame = respondent.value_frame if isinstance(respondent.value_frame, Mapping) else {}
    priorities = _coerce_str_list(value_frame.get("priority_rank"))
    value_parts: List[str] = []
    if priorities:
        value_parts.append(f"priority order: {' > '.join(priorities[:5])}")
    for key, label in (
            ("sustainability_orientation", "sustainability orientation"),
            ("price_sensitivity", "price sensitivity"),
            ("novelty_seeking", "novelty seeking"),
            ("brand_loyalty", "brand loyalty"),
            ("health_concern", "health concern"),
    ):
        value = value_frame.get(key)
        if isinstance(value, str) and value.strip():
            value_parts.append(f"{label}: {value.strip()}")
    if value_parts:
        lines.append(f"Decision framing: {'; '.join(value_parts)}")

    indicator_parts: List[str] = []
    ## random access to top 10  indicators, as some profiles have very long lists and we want to capture variety across profiles
    r10_indicators = random.sample(respondent.key_indicators, min(10, len(respondent.key_indicators))) if isinstance(respondent.key_indicators, Sequence) else []
    for indicator in r10_indicators:
        if not isinstance(indicator, Mapping):
            continue
        label = str(indicator.get("statement_label") or indicator.get("indicator_category") or "").strip()
        description = str(indicator.get("statement_description") or "").strip()
        if label and description:
            indicator_parts.append(f"{label}: {description}")
        elif label:
            indicator_parts.append(label)
        elif description:
            indicator_parts.append(description)
        ## include metrics if present and concise
        metrics = indicator.get("metrics",[])
        if isinstance(metrics, Sequence):
            for metric in metrics:
                if not isinstance(metric, Mapping):
                    continue
                description = str(metric.get("description") or "").strip()
                value = metric.get("value")
                unit = metric.get("unit")

                if not description or value is None or not unit:
                    continue

                indicator_parts.append(f"{description} ({value} {unit})")

    if indicator_parts:
        lines.append(f"Key indicators: {' | '.join(indicator_parts)}")

    reasoning = respondent.reasoning_policies if isinstance(respondent.reasoning_policies, Mapping) else {}
    purchase = reasoning.get("purchase_advice")
    if isinstance(purchase, Mapping):
        biases = _coerce_str_list(purchase.get("default_biases"))
        tradeoffs = _coerce_str_list(purchase.get("tradeoff_rules"))
        reasoning_parts: List[str] = []
        if biases:
            reasoning_parts.append(f"default biases: {', '.join(biases[:5])}")
        if tradeoffs:
            reasoning_parts.append(f"tradeoff rules: {', '.join(tradeoffs[:5])}")
        if reasoning_parts:
            lines.append(f"Reasoning guidance: {'; '.join(reasoning_parts)}")

    content_filters = respondent.content_filters if isinstance(respondent.content_filters, Mapping) else {}
    avoid_styles = _coerce_str_list(content_filters.get("avoid_styles"))
    disclaimers = _coerce_str_list(content_filters.get("emphasise_disclaimers_on"))
    filter_parts: List[str] = []
    if avoid_styles:
        filter_parts.append(f"avoid styles: {', '.join(avoid_styles[:5])}")
    if disclaimers:
        filter_parts.append(f"emphasise disclaimers on: {', '.join(disclaimers[:5])}")
    if filter_parts:
        lines.append(f"Content boundaries: {'; '.join(filter_parts)}")

    return "\n".join(lines)


def _build_response_generation_prompt(*, survey: Survey, respondent: RespondentProfile) -> str:
    survey_payload = {
        "survey_id": survey.survey_id,
        "title": survey.title,
        "description": survey.description,
        "questions": [
            {
                "question_id": question.question_id,
                "text": question.text,
                "type": question.type,
                "options": question.options,
                "metadata": question.metadata,
            }
            for question in survey.questions
        ],
    }
    respondent_description = _describe_respondent_for_prompt(respondent)

    return (
        f"{SURVEY_SIMULATION_PRIMING_PROMPT}\n\n"
        f"Respondent persona:\n{respondent_description}\n\n"
        f"Survey:\n{json.dumps(survey_payload, ensure_ascii=False, indent=2)}"
    )


def render_response_generation_prompt(*, survey: Survey, respondent: RespondentProfile) -> str:
    return _build_response_generation_prompt(survey=survey, respondent=respondent)
