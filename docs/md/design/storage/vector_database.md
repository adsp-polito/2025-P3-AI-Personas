# Storage: `VectorDatabase`

**Code**: `adsp/storage/vector_db.py`

## Purpose

`VectorDatabase` is a placeholder vector store used by the Core RAG pipeline to retrieve grounding context.

## Responsibilities

- Store persona-associated “documents” (currently strings)
- Return a relevant document for a query (currently naive)

## Public API

### `upsert(persona_id: str, document: str) -> None`

Appends `document` to the persona’s document list.

### `search(persona_id: str, query: str) -> str`

Returns the last stored document for the persona, or `""` if none exists.

## Data model

- `_documents: DefaultDict[str, List[str]]` (in-memory)

## Current usage

Used by:
- `adsp/core/rag/__init__.py` (`RAGPipeline.retrieve()` → `VectorDatabase.search()`)

## Key dependencies / technologies

- Python `dataclasses`
- `collections.defaultdict`

## Notes / production hardening

Replace with a real vector DB (FAISS/Chroma/Weaviate/Pinecone/etc.) plus:
- Embeddings model (e.g., `sentence-transformers` or `langchain-huggingface`)
- Metadata filters (persona_id, indicator domain/category, document/page ids)
- Source citations returned as structured data (not just a string)

If you plan to use LangChain’s in-memory vector store today, see:
- `docs/md/design/data_pipeline/indicator_rag.md`

