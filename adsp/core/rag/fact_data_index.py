"""Fact data RAG index for runtime retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from adsp.core.types import Citation, RetrievedContext
from adsp.data_pipeline.fact_data_pipeline.rag.indicator import (
    FactDataRAG,
    documents_to_context_prompt,
)

DEFAULT_EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"


def _default_embeddings() -> Embeddings:
    return HuggingFaceEmbeddings(model_name=DEFAULT_EMBEDDING_MODEL_NAME)


@dataclass
class FactDataRAGIndex:
    """In-memory similarity search over fact-data markdown chunks."""

    embeddings: Embeddings = field(default_factory=_default_embeddings)
    rag: FactDataRAG = field(init=False)
    indexed_chunk_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.rag = FactDataRAG(self.embeddings)

    def index_markdown_directory(self, directory: Path, *, pattern: str = "page_*.md") -> int:
        chunk_ids = self.rag.index_markdown_directory(Path(directory), pattern=pattern)
        self.indexed_chunk_ids.extend(chunk_ids)
        return len(chunk_ids)

    def search(self, query: str, *, k: int = 10) -> List[Document]:
        return self.rag.search(query, k=k)

    def retrieve(self, query: str, *, k: int = 10) -> RetrievedContext:
        docs = self.search(query, k=k)
        if not docs:
            return RetrievedContext(context="", citations=[], raw={"documents": []})

        citations = [self._citation_from_doc(doc) for doc in docs]
        raw_docs = [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
        return RetrievedContext(
            context=documents_to_context_prompt(docs),
            citations=citations,
            raw={"documents": raw_docs},
        )

    @staticmethod
    def _citation_from_doc(doc: Document) -> Citation:
        meta = doc.metadata or {}
        doc_id = meta.get("source_file") if isinstance(meta.get("source_file"), str) else None

        pages: List[int] = []
        page = meta.get("page_number") or meta.get("page")
        try:
            page_int = int(page)
            if page_int > 0:
                pages.append(page_int)
        except Exception:
            pass

        snippet = doc.page_content.strip()
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."

        segment = meta.get("segment") if isinstance(meta.get("segment"), str) else None
        section = meta.get("section") if isinstance(meta.get("section"), str) else None
        template = meta.get("template") if isinstance(meta.get("template"), str) else None
        label_parts = [value for value in (segment, section, template) if value]

        return Citation(
            doc_id=doc_id or "fact_data",
            pages=pages,
            domain="fact_data",
            category=segment or section,
            indicator_label=" | ".join(label_parts) if label_parts else "fact_data",
            snippet=snippet,
        )


def _safe_dir_has_files(directory: Path, *, pattern: str) -> bool:
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        return False
    return any(directory.glob(pattern))


def build_fact_data_index_from_markdown(
    markdown_dir: Path,
    *,
    embeddings: Optional[Embeddings] = None,
    pattern: str = "page_*.md",
) -> Optional[FactDataRAGIndex]:
    """Create and populate a fact-data index from a markdown directory."""

    if not _safe_dir_has_files(markdown_dir, pattern=pattern):
        return None

    index = FactDataRAGIndex(embeddings=embeddings or _default_embeddings())
    index.index_markdown_directory(markdown_dir, pattern=pattern)
    return index


__all__ = ["FactDataRAGIndex", "build_fact_data_index_from_markdown"]
