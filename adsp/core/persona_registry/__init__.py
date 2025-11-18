"""In-memory persona catalog."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

DEFAULT_PERSONA = {
    "preamble": "You are a Lavazza persona who is transparent and data-grounded.",
}


@dataclass
class PersonaRegistry:
    """Keeps persona metadata available for prompt construction and routing."""

    _personas: Dict[str, Dict] = field(default_factory=lambda: {"default": DEFAULT_PERSONA})

    def get(self, persona_id: str) -> Dict:
        try:
            return self._personas[persona_id]
        except KeyError as exc:  # pragma: no cover - defensive message
            raise KeyError(f"Persona '{persona_id}' is not registered") from exc

    def upsert(self, persona_id: str, metadata: Dict) -> None:
        self._personas[persona_id] = metadata
