"""Retrieval-Augmented Generation utilities."""

from __future__ import annotations

from dataclasses import dataclass

from adsp.storage.vector_db import VectorDatabase


@dataclass
class RAGPipeline:
    """Simple retriever placeholder backed by the vector database stub."""

    vector_db: VectorDatabase = VectorDatabase()

    def retrieve(self, persona_id: str, query: str) -> str:
        return self.vector_db.search(persona_id=persona_id, query=query)
