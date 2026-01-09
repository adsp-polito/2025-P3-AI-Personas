"""
Tests for prompt builder functionality.

Checks that prompts are constructed correctly with context and history.
"""

from adsp.core.prompt_builder import PromptBuilder


def test_build_prompt_basic():
    builder = PromptBuilder()
    prompt = builder.build(
        persona_id="default",
        query="hello",
        context="some context"
    )

    assert "hello" in prompt
    assert "some context" in prompt
    assert "QUESTION" in prompt


def test_build_prompt_with_history():
    builder = PromptBuilder()
    history = [
        {"query": "first question", "response": "first answer"},
        {"query": "second question", "response": "second answer"}
    ]

    prompt = builder.build(
        persona_id="default",
        query="third question",
        context="context here",
        history=history
    )

    assert "HISTORY" in prompt
    assert "first question" in prompt
    assert "third question" in prompt


def test_build_prompt_empty_history():
    builder = PromptBuilder()
    prompt = builder.build(
        persona_id="default",
        query="test query",
        context="test context",
        history=[]
    )

    # empty history shouldn't add HISTORY section
    assert "HISTORY" not in prompt or "Conversation history" not in prompt


def test_prompt_structure():
    builder = PromptBuilder()
    prompt = builder.build(
        persona_id="default",
        query="what's the weather?",
        context="current conditions"
    )

    # check basic structure exists
    assert "SYSTEM PROMPT" in prompt
    assert "CONTEXT" in prompt
    assert "QUESTION" in prompt
