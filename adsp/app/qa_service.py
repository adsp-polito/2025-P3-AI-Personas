"""Interactive Q&A experience surface."""

from __future__ import annotations

from dataclasses import dataclass

from adsp.core import orchestrator


@dataclass
class QAService:
    """Thin wrapper that forwards prompts to the orchestrator."""

    def ask(self, persona_id: str, query: str) -> str:
        """Send a query to the orchestrator and return the persona response."""

        engine = orchestrator.Orchestrator()
        return engine.handle_query(persona_id=persona_id, query=query)
