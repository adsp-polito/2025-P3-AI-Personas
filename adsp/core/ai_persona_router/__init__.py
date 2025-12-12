"""Routes prompts to persona-specific model endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field

from adsp.modeling.inference import PersonaInferenceEngine


@dataclass
class PersonaRouter:
    """Leverages persona metadata to pick the right PEFT adapter/model."""

    # inference_engine: PersonaInferenceEngine = PersonaInferenceEngine()
    inference_engine: PersonaInferenceEngine = field(default_factory=PersonaInferenceEngine)

    def dispatch(self, persona_id: str, prompt: str) -> str:
        return self.inference_engine.generate(persona_id=persona_id, prompt=prompt)
