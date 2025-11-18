"""Constructs prompts by mixing persona rules, query, and retrieved context."""

from __future__ import annotations

from dataclasses import dataclass

from adsp.core.persona_registry import PersonaRegistry


@dataclass
class PromptBuilder:
    registry: PersonaRegistry = PersonaRegistry()

    def build(self, persona_id: str, query: str, context: str) -> str:
        persona = self.registry.get(persona_id)
        preamble = persona.get("preamble", "You are an AI persona.")
        return f"{preamble}\n\nContext:\n{context}\n\nQuestion:\n{query}"
