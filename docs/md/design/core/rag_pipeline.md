# Core: `RAGPipeline`

**Code**: `adsp/core/rag/__init__.py`

## Purpose

`RAGPipeline` provides factual grounding by retrieving relevant context from the vector store given `(persona_id, query)`.

## Responsibilities

- Query the vector store for relevant evidence
- Return a context string to inject into prompt construction

## Public API

### `retrieve(persona_id: str, query: str) -> str`

**Inputs**
- `persona_id`: persona scope for retrieval
- `query`: normalized user query

**Output**
- context string

## Internal logic (current)

- Delegates to `VectorDatabase.search(persona_id, query)`

## Key dependencies / technologies

- `adsp/storage/vector_db.py` (`VectorDatabase`) — currently an in-memory stub

## Recommended upgrade path

This repo also contains a more realistic RAG component (LangChain-based):
- `adsp/data_pipeline/persona_data_pipeline/rag/indicator.py` (`PersonaIndicatorRAG`)

A practical integration pattern:
1. Load persona profiles (`PersonaProfileModel`) and index indicators into a vector store.
2. At query time, run similarity search and convert `Document[]` to a prompt-ready context string.
3. Return both context and structured citations for explainability.

See: `docs/md/design/integration/wiring_rag_into_orchestrator.md`

