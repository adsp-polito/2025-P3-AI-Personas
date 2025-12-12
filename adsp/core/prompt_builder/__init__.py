"""Constructs prompts by mixing persona rules, query, and retrieved context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from adsp.core.persona_registry import PersonaRegistry
from adsp.core.prompt_builder.system_prompt import persona_to_system_prompt
from adsp.data_pipeline.schema import PersonaProfileModel


@dataclass
class PromptBuilder:
    # registry: PersonaRegistry = PersonaRegistry()
    registry: PersonaRegistry = field(default_factory=PersonaRegistry)

    def build(self, persona_id: str, query: str, context: str, history: list[dict] | None = None) -> str:
        persona = self.registry.get(persona_id)
        # get system prompt from persona
        system_prompt = self._system_prompt_for_persona(persona)
        history_block = self._history_block(history)
        if history_block:
            return f"{system_prompt}\n\n{history_block}\n\nContext:\n{context}\n\nQuestion:\n{query}"
        return f"{system_prompt}\n\nContext:\n{context}\n\nQuestion:\n{query}"

    @staticmethod
    def _history_block(history: list[dict] | None) -> str:
        if not history:
            return ""
        lines = ["Conversation history (most recent last):"]
        for item in history[-10:]:
            if not isinstance(item, dict):
                continue
            q = item.get("query")
            r = item.get("response")
            if q:
                lines.append(f"- User: {q}")
            if r:
                lines.append(f"- Persona: {r}")
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    def _system_prompt_for_persona(self, persona: Any) -> str:
        if isinstance(persona, PersonaProfileModel):
            return persona_to_system_prompt(persona)

        if isinstance(persona, dict):
            has_reasoning_traits = any(
                key in persona
                for key in (
                    "style_profile",
                    "value_frame",
                    "reasoning_policies",
                    "content_filters",
                )
            )
            if has_reasoning_traits:
                try:
                    profile = PersonaProfileModel(**persona)
                    return persona_to_system_prompt(profile)
                except ValidationError:
                    pass
            # get value of preamble, otherwise use the default value
            return persona.get("preamble", "You are an AI persona.")

        return "You are an AI persona."


__all__ = ["PromptBuilder", "persona_to_system_prompt"]
