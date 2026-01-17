"""Fact data embedding and retrieval using LangChain primitives."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

# a fundamental data structure in LangChain to represent a piece of text content along with its metadata
from langchain_core.documents import Document
# an abstract base class for embedding models
from langchain_core.embeddings import Embeddings
# vector store interfaces for similarity search and retrieval
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from loguru import logger

from .chunker import FactDataMarkdownChunker


def _default_vectorstore(embeddings: Embeddings) -> VectorStore:
    try:
        from langchain_community.docstore.in_memory import InMemoryDocstore
        from langchain_community.vectorstores import FAISS
        import faiss  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "FAISS vectorstore requires `faiss-cpu` and `langchain-community` to be installed."
        ) from exc

    dim = len(embeddings.embed_query("dimension probe"))
    index = faiss.IndexFlatL2(dim)
    return FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )


class FactDataRAG:
    """Embeds fact indicators and exposes similarity search over them."""

    def __init__(
        self,
        embeddings: Embeddings,
        *,
        vectorstore: VectorStore | None = None,
        chunk_size: int = 1200,
        chunk_overlap: int = 50,
    ) -> None:
        self.embeddings = embeddings
        self.vectorstore = vectorstore or _default_vectorstore(embeddings)
        self.chunker = FactDataMarkdownChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def search(self, query: str, *, k: int = 10) -> List[Document]:
        """Similarity search against indexed facts."""
        return self.vectorstore.similarity_search(query, k=k)

    def as_retriever(self, *, k: int = 10) -> VectorStoreRetriever:
        """Expose a LangChain retriever with a fixed top-k."""
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def index_markdown_file(self, file_path: Path) -> List[str]:
        """Index a single markdown file by chunking and adding to vector store."""
        chunks = self.chunker.chunk_markdown_file(file_path)
        if not chunks:
            return []
        
        return self.vectorstore.add_documents(chunks)
    
    def index_markdown_directory(
        self,
        directory: Path,
        pattern: str = "page_*.md",
    ) -> List[str]:
        """Index all markdown files in a directory."""
        chunks = self.chunker.chunk_directory(directory, pattern)
        
        if not chunks:
            logger.warning(f"No chunks created from {directory}")
            return []
        
        logger.info(f"Indexing {len(chunks)} chunks into vector store")
        return self.vectorstore.add_documents(chunks)


def documents_to_context_prompt(documents: Iterable[Document]) -> str:
    """Convert search result documents into a context string for prompts."""
    blocks: List[str] = []
    for doc in documents:
        meta = doc.metadata or {}
        header_parts = []

        # Prioritize segment information
        if meta.get("segment"):
            header_parts.append(f"Segment: {meta['segment']}")
        if meta.get("section"):
            header_parts.append(f"Section: {meta['section']}")
        if meta.get("template"):
            header_parts.append(f"Template: {meta['template']}")
        if meta.get("page_number") or meta.get("page"):
            page = meta.get("page_number") or meta.get("page")
            header_parts.append(f"Page: {page}")
        if meta.get("source_file"):
            header_parts.append(f"Source: {meta['source_file']}")
        
        header = " | ".join(header_parts)
        body = doc.page_content.strip()

        block_lines = [header] if header else []
        block_lines.append(body)
        blocks.append("\n".join(line for line in block_lines if line))

    return "\n\n---\n\n".join(blocks)


__all__ = ["FactDataRAG", "documents_to_context_prompt"]
