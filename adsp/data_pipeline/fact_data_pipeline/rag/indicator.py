"""Fact data embedding and retrieval using LangChain primitives."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Iterable, List

# a fundamental data structure in LangChain to represent a piece of text content along with its metadata
from langchain_core.documents import Document

# an abstract base class for embedding models
from langchain_core.embeddings import Embeddings

# vector store interfaces for similarity search and retrieval
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from loguru import logger

from adsp.storage.langchain_vectorstore import build_vectorstore
from adsp.utils.progress import progress_bar

from .chunker import FactDataMarkdownChunker

DEFAULT_INDEXING_BATCH_SIZE = 128


class FactDataRAG:
    """Embeds fact indicators and exposes similarity search over them."""

    def __init__(
        self,
        embeddings: Embeddings,
        *,
        vectorstore: VectorStore | None = None,
        namespace: str = "fact-data",
        chunk_size: int = 1200,
        chunk_overlap: int = 50,
    ) -> None:
        self.embeddings = embeddings
        self.vectorstore = vectorstore or build_vectorstore(embeddings, namespace=namespace)
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
        pattern: str = "*.md",
    ) -> List[str]:
        """Index all markdown files in a directory."""
        start_time = time.perf_counter()
        chunks = self.chunker.chunk_directory(directory, pattern)
        
        if not chunks:
            logger.warning(f"No chunks created from {directory}")
            return []
        
        logger.info(
            "Indexing step 1/2 complete: prepared {} chunks from {}",
            len(chunks),
            directory,
        )
        logger.info("Indexing step 2/2: writing chunks into vector store")
        chunk_ids: List[str] = []
        total_batches = max(1, (len(chunks) + DEFAULT_INDEXING_BATCH_SIZE - 1) // DEFAULT_INDEXING_BATCH_SIZE)
        with progress_bar(
            total=len(chunks),
            desc="Indexing chunks",
            unit="chunk",
            leave=False,
        ) as progress:
            for batch_idx, start in enumerate(range(0, len(chunks), DEFAULT_INDEXING_BATCH_SIZE), start=1):
                batch = chunks[start : start + DEFAULT_INDEXING_BATCH_SIZE]
                chunk_ids.extend(self.vectorstore.add_documents(batch))
                progress.update(len(batch))
                progress.set_postfix(batch=f"{batch_idx}/{total_batches}")
        logger.info(
            "Indexing complete: stored {} chunks in {:.2f}s",
            len(chunk_ids),
            time.perf_counter() - start_time,
        )
        return chunk_ids


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
