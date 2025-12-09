"""Persona indicator embedding and retrieval using LangChain primitives."""

from __future__ import annotations

from typing import Iterable, List, Tuple

# a fundamental data structure in LangChain to represent a piece of text content along with its metadata
from langchain_core.documents import Document
# an abstract base class for embedding models
from langchain_core.embeddings import Embeddings
# import a basic, in-memory vector database implementation provided by LangChain, and an interface for retrieving
# Documents from a vector store based on query
from langchain_core.vectorstores import InMemoryVectorStore, VectorStoreRetriever

from adsp.data_pipeline.schema import Fact, FactDocument


class FactDataIndicatorRAG:
    """Embeds fact indicators and exposes similarity search over them."""

    def __init__(
        self,
        embeddings: Embeddings,
        *,
        vectorstore: InMemoryVectorStore | None = None,
    ) -> None:
        self.embeddings = embeddings
        self.vectorstore = vectorstore or InMemoryVectorStore(embedding=embeddings)

    def index_fact_document(self, fact_document: FactDocument) -> List[str]:
        """Add a document's facts to the vector store."""
        texts, metadatas = self._fact_payloads(fact_document)
        if not texts:
            return []
        return self.vectorstore.add_texts(texts=texts, metadatas=metadatas)

    def index_fact_documents(self, fact_documents: Iterable[FactDocument]) -> List[str]:
        """Batch index multiple fact documents."""
        ids: List[str] = []
        for doc in fact_documents:
            ids.extend(self.index_fact_document(doc))
        return ids

    def search(self, query: str, *, k: int = 5) -> List[Document]:
        """Similarity search against indexed facts."""
        return self.vectorstore.similarity_search(query, k=k)

    def as_retriever(self, *, k: int = 5) -> VectorStoreRetriever:
        """Expose a LangChain retriever with a fixed top-k."""
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def _fact_payloads(self, fact_document: FactDocument) -> Tuple[List[str], List[dict]]:
        """Helper method to prepare data for indexing."""
        texts: List[str] = []
        metadatas: List[dict] = []

        for page in fact_document.pages:
            for fact in page.elements:
                text = self._render_fact(fact, page.page_number)
                if not text:
                    continue

                texts.append(text)
                metadatas.append(
                    {
                        "document_id": fact_document.document_id,
                        "page_number": page.page_number,
                        "element_id": fact.id,
                        "element_type": fact.type,
                    }
                )

        return texts, metadatas

    def _render_fact(self, fact: Fact, page_number: int) -> str:
        """Render a fact into a string for embedding."""
        parts: List[str] = []

        if fact.type:
            parts.append(f"Type: {fact.type}")
        
        parts.append(f"Page: {page_number}")

        if fact.text:
            parts.append(fact.text)

        if fact.structured_content:
            # Basic rendering of structured content. This could be more sophisticated.
            import json
            parts.append("Structured Content:")
            parts.append(json.dumps(fact.structured_content, indent=2))

        return "\n".join(parts).strip()


def documents_to_context_prompt(documents: Iterable[Document]) -> str:
    """Convert search result documents into a context string for prompts."""
    blocks: List[str] = []
    for doc in documents:
        meta = doc.metadata or {}
        header_parts = []

        if meta.get("document_id"):
            header_parts.append(f"Document: {meta['document_id']}")
        if meta.get("page_number"):
            header_parts.append(f"Page: {meta['page_number']}")
        if meta.get("element_type"):
            header_parts.append(f"Type: {meta['element_type']}")
        if meta.get("element_id"):
            header_parts.append(f"ID: {meta['element_id']}")
        
        header = " | ".join(header_parts)
        body = doc.page_content.strip()

        block_lines = [header] if header else []
        block_lines.append(body)
        blocks.append("\n".join(line for line in block_lines if line))

    return "\n\n---\n\n".join(blocks)


__all__ = ["FactDataIndicatorRAG", "documents_to_context_prompt"]