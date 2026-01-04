"""Local RAG index over persona indicators."""

from __future__ import annotations

import math
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from adsp.core.types import Citation, RetrievedContext
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import (
    PersonaIndicatorRAG,
    documents_to_context_prompt,
)
from adsp.data_pipeline.schema import PersonaProfileModel


class HashEmbeddings(Embeddings):
    """Deterministic local embeddings with no external model downloads.

    This is intentionally simple: it uses token hashing into a fixed-size vector.
    """

    def __init__(self, dim: int = 384) -> None:
        if dim <= 0:
            raise ValueError("dim must be > 0")
        self.dim = dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dim
        if not text:
            return vector

        for raw_token in text.lower().split():
            token = "".join(ch for ch in raw_token if ch.isalnum() or ch in ("-", "_"))
            if not token:
                continue
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            h = int.from_bytes(digest, "big", signed=False)
            idx = h % self.dim
            vector[idx] += 1.0 if (h & 1) else -1.0

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


@dataclass
class PersonaRAGIndex:
    """Builds and queries per-persona indicator vector stores."""

    embeddings: Embeddings = field(default_factory=HashEmbeddings)
    _indexes: Dict[str, PersonaIndicatorRAG] = field(default_factory=dict)

    def index_personas(self, personas: Iterable[PersonaProfileModel]) -> None:
        for persona in personas:
            if not persona.persona_id:
                continue
            rag = PersonaIndicatorRAG(self.embeddings)
            rag.index_persona(persona)
            self._indexes[persona.persona_id] = rag

    def has_persona(self, persona_id: str) -> bool:
        return persona_id in self._indexes

    def search(self, persona_id: str, query: str, *, k: int = 5) -> List[Document]:
        rag = self._indexes.get(persona_id)
        if rag is None:
            return []
        return rag.search(query, k=k)

    def retrieve(self, persona_id: str, query: str, *, k: int = 5) -> RetrievedContext:
        docs = self.search(persona_id, query, k=k)
        context = documents_to_context_prompt(docs) if docs else ""
        citations = [self._citation_from_doc(doc) for doc in docs]
        citations = [c for c in citations if c is not None]
        raw_docs = [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
        return RetrievedContext(
            context=context,
            citations=citations,  # type: ignore[arg-type]
            raw={"documents": raw_docs},
        )

    @staticmethod
    def _citation_from_doc(doc: Document) -> Optional[Citation]:
        meta = doc.metadata or {}
        sources = meta.get("sources")

        doc_id = None
        pages: List[int] = []
        if isinstance(sources, list) and sources:
            first = sources[0]
            if isinstance(first, dict):
                doc_id = first.get("doc_id") if isinstance(first.get("doc_id"), str) else None
                raw_pages = first.get("pages")
                if isinstance(raw_pages, list):
                    for value in raw_pages:
                        try:
                            pages.append(int(value))
                        except Exception:
                            continue

        snippet = doc.page_content.strip()
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."

        return Citation(
            doc_id=doc_id,
            pages=pages,
            persona_id=meta.get("persona_id"),
            indicator_id=meta.get("indicator_id"),
            indicator_label=meta.get("indicator_label"),
            domain=meta.get("domain"),
            category=meta.get("category"),
            snippet=snippet,
        )


__all__ = ["HashEmbeddings", "PersonaRAGIndex"]
