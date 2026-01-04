"""Turn persona profiles into LLM-ready system prompts."""

from __future__ import annotations

from typing import Iterable, Optional

from adsp.data_pipeline.schema import (
    ContentFilters,
    PersonaProfileModel,
    ReasoningPolicies,
    StyleProfile,
    ValueFrame,
)


def persona_to_system_prompt(persona: PersonaProfileModel, display_name: Optional[str] = None) -> str:
    """Convert a persona profile (with reasoning traits) into a system prompt."""
    persona_label = persona.persona_name or persona.persona_id or "the persona"
    if persona.persona_id and persona.persona_name:
        persona_label = f'{persona.persona_name} (id: {persona.persona_id})'

    header_lines = [f'You are persona "{persona_label}".']
    
    if display_name and display_name != persona.persona_name:
        header_lines.append(f"For this conversation, your name is '{display_name}'.")
    
    if persona.summary_bio:
        header_lines.append(f"Summary: {persona.summary_bio}")

    sections = [
        "\n".join(header_lines),
        _style_section(persona.style_profile),
        _value_frame_section(persona.value_frame),
        _reasoning_policies_section(persona.reasoning_policies),
        _content_filters_section(persona.content_filters),
        _answering_guidelines_section(),
        (
            "Stay in this voice, respect the value priorities and tradeoff rules, and "
            "surface disclaimers when filters apply."
        ),
    ]
    return "\n\n".join([section for section in sections if section])


def _style_section(style: Optional[StyleProfile]) -> Optional[str]:
    if not style:
        return None

    lines = ["Voice:"]
    if style.tone_adjectives:
        lines.append(f"- Tone adjectives: {_join(style.tone_adjectives)}")

    delivery = []
    if style.formality_level:
        delivery.append(f"formality={style.formality_level}")
    if style.directness:
        delivery.append(f"directness={style.directness}")
    if style.emotional_flavour:
        delivery.append(f"emotional_flavour={style.emotional_flavour}")
    if style.criticality_level:
        delivery.append(f"criticality={style.criticality_level}")
    if delivery:
        lines.append(f"- Delivery: {'; '.join(delivery)}")

    if style.verbosity_preference:
        lines.append(f"- Verbosity: {style.verbosity_preference}")
    if style.preferred_structures:
        lines.append(f"- Preferred structures: {_join(style.preferred_structures)}")
    if style.typical_register_examples:
        lines.append(f"- Register examples: {_join(style.typical_register_examples)}")
    return "\n".join(lines)


def _value_frame_section(value_frame: Optional[ValueFrame]) -> Optional[str]:
    if not value_frame:
        return None

    lines = ["Value frame:"]
    if value_frame.priority_rank:
        lines.append(f"- Priority order: {' > '.join(value_frame.priority_rank)}")

    sensitivities = []
    if value_frame.sustainability_orientation:
        sensitivities.append(f"sustainability={value_frame.sustainability_orientation}")
    if value_frame.price_sensitivity:
        sensitivities.append(f"price_sensitivity={value_frame.price_sensitivity}")
    if value_frame.novelty_seeking:
        sensitivities.append(f"novelty_seeking={value_frame.novelty_seeking}")
    if value_frame.brand_loyalty:
        sensitivities.append(f"brand_loyalty={value_frame.brand_loyalty}")
    if value_frame.health_concern:
        sensitivities.append(f"health_concern={value_frame.health_concern}")
    if sensitivities:
        lines.append(f"- Sensitivities: {'; '.join(sensitivities)}")

    if value_frame.description:
        lines.append(f"- Summary: {value_frame.description}")
    return "\n".join(lines)


def _reasoning_policies_section(policies: Optional[ReasoningPolicies]) -> Optional[str]:
    if not policies:
        return None

    lines = ["Reasoning policies:"]
    if policies.purchase_advice:
        purchase = []
        if policies.purchase_advice.default_biases:
            purchase.append(f"biases: {_join(policies.purchase_advice.default_biases)}")
        if policies.purchase_advice.tradeoff_rules:
            purchase.append(f"tradeoff rules: {_join(policies.purchase_advice.tradeoff_rules)}")
        if purchase:
            lines.append(f"- Purchase advice: {'; '.join(purchase)}")

    if policies.product_evaluation:
        evaluation = []
        if policies.product_evaluation.praise_triggers:
            evaluation.append(
                f"praise triggers: {_join(policies.product_evaluation.praise_triggers)}"
            )
        if policies.product_evaluation.criticism_triggers:
            evaluation.append(
                f"criticism triggers: {_join(policies.product_evaluation.criticism_triggers)}"
            )
        if policies.product_evaluation.must_always_check:
            evaluation.append(
                f"must always check: {_join(policies.product_evaluation.must_always_check)}"
            )
        if evaluation:
            lines.append(f"- Product evaluation: {'; '.join(evaluation)}")

    if policies.information_processing:
        info = []
        if policies.information_processing.trust_preference:
            info.append(f"trust: {_join(policies.information_processing.trust_preference)}")
        if policies.information_processing.scepticism_towards:
            info.append(
                f"sceptical of: {_join(policies.information_processing.scepticism_towards)}"
            )
        if policies.information_processing.requested_rigor_level:
            info.append(f"rigor={policies.information_processing.requested_rigor_level}")
        if info:
            lines.append(f"- Information processing: {'; '.join(info)}")

    if len(lines) == 1:
        return None
    return "\n".join(lines)


def _content_filters_section(filters: Optional[ContentFilters]) -> Optional[str]:
    if not filters:
        return None

    lines = ["Content filters:"]
    if filters.avoid_styles:
        lines.append(f"- Avoid styles: {_join(filters.avoid_styles)}")
    if filters.emphasise_disclaimers_on:
        lines.append(f"- Emphasise disclaimers on: {_join(filters.emphasise_disclaimers_on)}")

    if len(lines) == 1:
        return None
    return "\n".join(lines)


def _join(values: Iterable[str], sep: str = ", ") -> str:
    return sep.join(str(v) for v in values if v)


def preamble_to_system_prompt(preamble: str | None, display_name: str | None = None) -> str:
    """Wrap a plain persona preamble with consistent response rules."""

    base = (preamble or "").strip() or "You are an AI persona."
    
    if display_name:
        base = f"{base}\n\nFor this conversation, your name is '{display_name}'."
    
    sections = [
        base,
        _answering_guidelines_section(),
    ]
    return "\n\n".join(section for section in sections if section)


def _answering_guidelines_section() -> str:
    return "\n".join(
        [
"""

**Answering Rules (Strict):**

* Answer **only** the user’s question. Nothing extra.
* Do not volunteer information about coffee, products, or related topics unless the user asks about them.
* Use context **only if it directly changes the answer**; otherwise ignore it.
* If essential info is missing, ask **one clear clarifying question**.
* Write like a real professional, not a system or narrator.
* Keep responses **as short as possible** while still correct (1–2 sentences for simple questions).
* No background explanations, side facts, or prompt restatement unless explicitly requested.

**Persona Requirements (only when relevant):**

* Maintain a consistent professional background with clear career progression.
* Reflect a realistic daily routine aligned with that profession.
* Let personality traits influence tone and decision-making.
* Demonstrate specific, measurable skills through answers—not descriptions.

**Priority:**
Clarity > Brevity > Accuracy.
No overthinking. No embellishment. Answer the question directly.
        """

        ]
    )
