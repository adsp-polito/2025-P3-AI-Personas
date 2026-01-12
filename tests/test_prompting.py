"""
Tests for prompt builder and system prompt formatting.
"""

from adsp.core.persona_registry import PersonaRegistry
from adsp.core.prompt_builder import PromptBuilder
from adsp.core.prompt_builder.system_prompt import (
    persona_to_system_prompt,
    preamble_to_system_prompt,
)
from adsp.data_pipeline.schema import (
    ContentFilters,
    PersonaProfileModel,
    ReasoningPolicies,
    StyleProfile,
    ValueFrame,
    PurchaseAdvice,
    ProductEvaluation,
    InformationProcessing,
)


def test_prompt_builder_build_with_default_persona():
    registry = PersonaRegistry()
    builder = PromptBuilder(registry=registry)
    prompt = builder.build("default", "hello", "context")
    assert "SYSTEM PROMPT" in prompt
    assert "QUESTION" in prompt
    assert "hello" in prompt


def test_prompt_builder_build_with_custom_preamble():
    registry = PersonaRegistry()
    registry.upsert("p1", {"preamble": "You are a helper."})
    builder = PromptBuilder(registry=registry)
    prompt = builder.build("p1", "question", "context")
    assert "You are a helper." in prompt


def test_prompt_builder_build_with_profile():
    registry = PersonaRegistry()
    profile = PersonaProfileModel(persona_id="p1", persona_name="Alpha")
    registry.upsert("p1", profile)
    builder = PromptBuilder(registry=registry)
    prompt = builder.build("p1", "question", "context")
    assert "Alpha" in prompt


def test_prompt_builder_history_block_uses_recent_items():
    builder = PromptBuilder(registry=PersonaRegistry())
    history = [
        {"query": "q1", "response": "a1"},
        {"query": "q2", "response": "a2"},
    ]
    block = builder._history_block(history)
    assert "Conversation history" in block
    assert "q1" in block
    assert "a2" in block


def test_prompt_builder_history_block_limits_to_ten():
    builder = PromptBuilder(registry=PersonaRegistry())
    history = [{"query": f"q{i}", "response": f"a{i}"} for i in range(12)]
    block = builder._history_block(history)
    assert "q0" not in block
    assert "q2" in block


def test_persona_to_system_prompt_minimal():
    persona = PersonaProfileModel(persona_id="p1", persona_name="Alpha")
    prompt = persona_to_system_prompt(persona)
    assert "You are persona" in prompt
    assert "Alpha" in prompt


def test_persona_to_system_prompt_uses_display_name():
    persona = PersonaProfileModel(persona_id="p1", persona_name="Alpha")
    prompt = persona_to_system_prompt(persona, display_name="Agent")
    assert "name is 'Agent'" in prompt


def test_persona_to_system_prompt_uses_summary():
    persona = PersonaProfileModel(persona_id="p1", summary_bio="Short summary")
    prompt = persona_to_system_prompt(persona)
    assert "Summary: Short summary" in prompt


def test_persona_to_system_prompt_style_section():
    persona = PersonaProfileModel(
        persona_id="p1",
        style_profile=StyleProfile(
            tone_adjectives=["warm", "direct"],
            formality_level="low",
            directness="high",
            verbosity_preference="short",
            preferred_structures=["bullets"],
        ),
    )
    prompt = persona_to_system_prompt(persona)
    assert "Voice:" in prompt
    assert "warm" in prompt
    assert "formality=low" in prompt
    assert "directness=high" in prompt
    assert "Verbosity: short" in prompt


def test_persona_to_system_prompt_value_frame_section():
    persona = PersonaProfileModel(
        persona_id="p1",
        value_frame=ValueFrame(
            priority_rank=["quality", "price"],
            price_sensitivity="medium",
            description="Focus on value",
        ),
    )
    prompt = persona_to_system_prompt(persona)
    assert "Value frame:" in prompt
    assert "quality > price" in prompt
    assert "price_sensitivity=medium" in prompt


def test_persona_to_system_prompt_reasoning_policies_section():
    policies = ReasoningPolicies(
        purchase_advice=PurchaseAdvice(
            default_biases=["eco"],
            tradeoff_rules=["price over brand"],
        ),
        product_evaluation=ProductEvaluation(
            praise_triggers=["durable"],
            criticism_triggers=["noisy"],
            must_always_check=["warranty"],
        ),
        information_processing=InformationProcessing(
            trust_preference=["official"],
            scepticism_towards=["ads"],
            requested_rigor_level="high",
        ),
    )
    persona = PersonaProfileModel(persona_id="p1", reasoning_policies=policies)
    prompt = persona_to_system_prompt(persona)
    assert "Reasoning policies:" in prompt
    assert "biases: eco" in prompt
    assert "tradeoff rules" in prompt
    assert "praise triggers" in prompt
    assert "Information processing" in prompt
    assert "rigor=high" in prompt


def test_persona_to_system_prompt_content_filters_section():
    persona = PersonaProfileModel(
        persona_id="p1",
        content_filters=ContentFilters(
            avoid_styles=["casual"],
            emphasise_disclaimers_on=["health"],
        ),
    )
    prompt = persona_to_system_prompt(persona)
    assert "Content filters:" in prompt
    assert "Avoid styles" in prompt


def test_preamble_to_system_prompt_default_fallback():
    prompt = preamble_to_system_prompt(None)
    assert "You are an AI persona." in prompt


def test_preamble_to_system_prompt_uses_display_name():
    prompt = preamble_to_system_prompt("Base", display_name="Agent")
    assert "name is 'Agent'" in prompt
