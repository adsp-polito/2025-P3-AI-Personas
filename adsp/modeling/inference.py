"""Persona inference utilities wrapping PEFT adapters and RAG outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PersonaInferenceEngine:
    """Placeholder inference engine; replace with actual LLM serving stack."""

    def generate(self, persona_id: str, prompt: str) -> str:
        return f"[{persona_id}] {prompt[:200]}"
