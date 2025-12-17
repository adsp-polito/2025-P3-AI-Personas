"""Retrieval-Augmented Generation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from adsp.core.rag.persona_index import PersonaRAGIndex
from adsp.core.types import RetrievedContext
from adsp.storage.vector_db import VectorDatabase


@dataclass
class RAGPipeline:
    """Retriever used by the runtime orchestrator.

    The pipeline supports two modes:
    - Persona indicator RAG (preferred for local demo): `persona_index`
    - Fallback string store: `vector_db`
    """

    vector_db: VectorDatabase = field(default_factory=VectorDatabase)
    persona_index: Optional[PersonaRAGIndex] = None

    def retrieve(self, persona_id: str, query: str, *, k: int = 5) -> str:
        return self.retrieve_with_metadata(persona_id=persona_id, query=query, k=k).context

    def retrieve_with_metadata(self, persona_id: str, query: str, *, k: int = 5) -> RetrievedContext:
        if self.persona_index and self.persona_index.has_persona(persona_id):
            return self.persona_index.retrieve(persona_id, query, k=k)
        return RetrievedContext(context=self.vector_db.search(persona_id=persona_id, query=query))


__all__ = ["RAGPipeline"]
