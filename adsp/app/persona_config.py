"""Persona configuration workflows surfaced to the frontend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PersonaConfigurationService:
    """Stores and retrieves persona definitions used by the orchestration core."""

    _personas: Dict[str, Dict] = field(default_factory=dict)

    def register_persona(self, persona_id: str, definition: Dict) -> None:
        """Persist a persona definition so that the Core layer can retrieve it."""

        self._personas[persona_id] = definition

    def list_personas(self) -> List[str]:
        """Return identifiers for the personas currently available in the system."""

        return sorted(self._personas.keys())

    def get_persona(self, persona_id: str) -> Dict:
        """Return a single persona definition, raising if it does not exist."""

        try:
            return self._personas[persona_id]
        except KeyError as exc:  # pragma: no cover - defensive message
            raise KeyError(f"Persona '{persona_id}' is not registered") from exc
