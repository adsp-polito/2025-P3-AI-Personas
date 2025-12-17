"""In-memory persona catalog."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

DEFAULT_PERSONA = {
    "preamble": "You are a Lavazza persona who is transparent and data-grounded.",
}


@dataclass
class PersonaRegistry:
    """Keeps persona metadata available for prompt construction and routing."""

    _personas: Dict[str, Any] = field(default_factory=lambda: {"default": DEFAULT_PERSONA})

    def get(self, persona_id: str) -> Any:
        try:
            return self._personas[persona_id]
        except KeyError as exc:  # pragma: no cover - defensive message
            raise KeyError(f"Persona '{persona_id}' is not registered") from exc

    def upsert(self, persona_id: str, metadata: Any) -> None:
        self._personas[persona_id] = metadata

    def upsert_many(self, personas: Iterable[tuple[str, Any]]) -> None:
        for persona_id, metadata in personas:
            self.upsert(persona_id, metadata)

    def list_personas(self) -> List[str]:
        return sorted(self._personas.keys())
