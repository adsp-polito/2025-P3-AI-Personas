"""Interactive Q&A experience surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from adsp.core.runtime import build_default_orchestrator
from adsp.core.types import ChatRequest, ChatResponse
from adsp.core.orchestrator import Orchestrator


@dataclass
class QAService:
    """Thin wrapper that forwards prompts to the orchestrator."""

    orchestrator: Orchestrator = field(default_factory=build_default_orchestrator)

    def ask(self, persona_id: str, query: str) -> str:
        """Send a query to the orchestrator and return the persona response."""

        return self.orchestrator.handle_query(persona_id=persona_id, query=query)

    def ask_with_metadata(
        self,
        *,
        persona_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> ChatResponse:
        """Return a structured response including retrieved context and citations."""

        return self.orchestrator.handle(
            ChatRequest(persona_id=persona_id, query=query, session_id=session_id, top_k=top_k)
        )
