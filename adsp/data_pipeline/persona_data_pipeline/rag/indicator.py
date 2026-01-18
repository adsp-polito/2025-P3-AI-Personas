"""Persona indicator embedding and retrieval using LangChain primitives."""

from __future__ import annotations

from typing import Iterable, List, Tuple

# a fundamental data structure in LangChain to represent a piece of text content along with its metadata
from langchain_core.documents import Document

# an abstract base class for embedding models
from langchain_core.embeddings import Embeddings

# vector store interfaces for similarity search and retrieval
from langchain_core.vectorstores import VectorStore, VectorStoreRetriever

from adsp.data_pipeline.schema import Indicator, PersonaProfileModel, Statement


def _get_embedding_dimension(embeddings: Embeddings) -> int:
    """Get the dimension of the embedding model.
    
    First checks if the embeddings object has a 'dim' attribute.
    Otherwise, computes it once by embedding a probe string.
    """
    # Check if the embeddings object exposes dimension directly
    if hasattr(embeddings, 'dim'):
        return embeddings.dim  # type: ignore[attr-defined]
    
    # Compute dimension by embedding a probe string
    # Cache the result on the embeddings object to avoid recomputation
    if not hasattr(embeddings, '_cached_dimension'):
        probe_vector = embeddings.embed_query("dimension probe")
        embeddings._cached_dimension = len(probe_vector)  # type: ignore[attr-defined]
    
    return embeddings._cached_dimension  # type: ignore[attr-defined]


def _default_vectorstore(embeddings: Embeddings) -> VectorStore:
    try:
        import faiss  # type: ignore
        from langchain_community.docstore.in_memory import InMemoryDocstore
        from langchain_community.vectorstores import FAISS
    except Exception as exc:
        raise RuntimeError(
            "FAISS vectorstore requires `faiss-cpu` and `langchain-community` to be installed."
        ) from exc

    dim = _get_embedding_dimension(embeddings)
    index = faiss.IndexFlatL2(dim)
    return FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )


class PersonaIndicatorRAG:
    """Embeds persona indicators and exposes similarity search over them."""

    def __init__(
        self,
        embeddings: Embeddings,
        *,
        vectorstore: VectorStore | None = None,
    ) -> None:
        self.embeddings = embeddings
        self.vectorstore = vectorstore or _default_vectorstore(embeddings)

    def index_persona(self, persona: PersonaProfileModel) -> List[str]:
        """Add a persona's indicators to the vector store, so index all indicators of the given persona"""
        # for each indicator of the persona generate text content and associated metadata
        texts, metadatas = self._indicator_payloads(persona)
        if not texts:
            return []
        # add_texts method of the vectorstore is used to embed the generated texts and store them along with their metadatas. This is where
        # the embedding model (provided in __init__) is used
        return self.vectorstore.add_texts(texts=texts, metadatas=metadatas)

    def index_personas(self, personas: Iterable[PersonaProfileModel]) -> List[str]:
        """Batch index multiple personas."""
        ids: List[str] = []
        for persona in personas:
            ids.extend(self.index_persona(persona))
        return ids

    def search(self, query: str, *, k: int = 5) -> List[Document]:
        """Similarity search against indexed indicators."""
        return self.vectorstore.similarity_search(query, k=k)

    def as_retriever(self, *, k: int = 5) -> VectorStoreRetriever:
        """Expose a LangChain retriever with a fixed top-k."""
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def _indicator_payloads(self, persona: PersonaProfileModel) -> Tuple[List[str], List[dict]]:
        """Helper method to prepare data for indexing. It will return a tuple of two lists: texts (the content to embed) and metadatas (associated dictionaries)"""
        texts: List[str] = []
        metadatas: List[dict] = []

        for indicator in persona.indicators:
            # convert the structured Indicator object into a readable text string. If the rendering results is an empty string, it skips this indicator
            text = self._render_indicator(persona, indicator)
            if not text:
                continue

            sources_payload = []
            for source in indicator.sources or []:
                sources_payload.append(
                    {
                        "doc_id": source.doc_id,
                        "pages": list(source.pages or []),
                    }
                )

            texts.append(text)
            metadatas.append(
                {
                    "persona_id": persona.persona_id,
                    "persona_name": persona.persona_name,
                    "indicator_id": indicator.id,
                    "indicator_label": indicator.label,
                    "domain": indicator.domain,
                    "category": indicator.category,
                    "sources": sources_payload,
                }
            )

        return texts, metadatas

    def _render_indicator(self, persona: PersonaProfileModel, indicator: Indicator) -> str:
        parts: List[str] = []

        persona_label = persona.persona_name or persona.persona_id
        indicator_label = indicator.label or indicator.id

        if persona_label or indicator_label:
            parts.append(
                " ".join(
                    value
                    for value in (
                        f"Persona: {persona_label}" if persona_label else "",
                        f"Indicator: {indicator_label}" if indicator_label else "",
                    )
                    if value
                )
            )

        for value in (indicator.domain, indicator.category, indicator.description):
            if value:
                parts.append(str(value))

        if indicator.statements:
            stmt_lines = [self._render_statement(stmt) for stmt in indicator.statements]
            stmt_lines = [line for line in stmt_lines if line]
            if stmt_lines:
                parts.append("Statements: " + " | ".join(stmt_lines))

        return "\n".join(parts).strip()

    def _render_statement(self, statement: Statement) -> str:
        elements: List[str] = []
        if statement.label:
            elements.append(statement.label)
        if statement.description:
            elements.append(statement.description)

        metrics = self._render_metrics(statement)
        if metrics:
            elements.append(f"metrics: {metrics}")

        if statement.salience:
            salience_bits = []
            if statement.salience.direction:
                salience_bits.append(f"salience={statement.salience.direction}")
            if statement.salience.magnitude:
                salience_bits.append(f"strength={statement.salience.magnitude}")
            if salience_bits:
                elements.append("; ".join(salience_bits))

        return "; ".join(elements)

    @staticmethod
    def _render_metrics(statement: Statement) -> str:
        if not statement.metrics:
            return ""

        metric_chunks: List[str] = []
        for metric in statement.metrics:
            parts = []
            if metric.value is not None:
                parts.append(str(metric.value))
            if metric.unit:
                parts.append(metric.unit)
            if metric.description:
                parts.append(metric.description)
            if parts:
                metric_chunks.append(" ".join(parts))

        return ", ".join(metric_chunks)


def documents_to_context_prompt(documents: Iterable[Document]) -> str:
    """Convert search result documents into a context string for prompts."""
    blocks: List[str] = []
    for doc in documents:
        meta = doc.metadata or {}
        header_parts = []

        persona_label = meta.get("persona_name") or meta.get("persona_id")
        indicator_label = meta.get("indicator_label") or meta.get("indicator_id")

        if persona_label:
            header_parts.append(f"Persona: {persona_label}")
        if indicator_label:
            header_parts.append(f"Indicator: {indicator_label}")
        if meta.get("domain"):
            header_parts.append(f"Domain: {meta['domain']}")
        if meta.get("category"):
            header_parts.append(f"Category: {meta['category']}")

        sources = meta.get("sources")
        if isinstance(sources, list) and sources:
            first = sources[0]
            if isinstance(first, dict):
                doc_id = first.get("doc_id")
                pages = first.get("pages")
                if isinstance(doc_id, str) and doc_id:
                    if isinstance(pages, list) and pages:
                        header_parts.append(f"Source: {doc_id} pages={pages}")
                    else:
                        header_parts.append(f"Source: {doc_id}")

        header = " | ".join(header_parts)
        body = doc.page_content.strip()

        block_lines = [header] if header else []
        block_lines.append(body)
        blocks.append("\n".join(line for line in block_lines if line))

    return "\n\n---\n\n".join(blocks)


__all__ = ["PersonaIndicatorRAG", "documents_to_context_prompt"]
