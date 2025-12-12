# Data Pipeline: `PersonaIndicatorRAG`

**Code**: `adsp/data_pipeline/persona_data_pipeline/rag/indicator.py`

## Purpose

`PersonaIndicatorRAG` provides a retrieval system over persona indicators using LangChain primitives. It is a more realistic implementation of the RAG concept than the Core `VectorDatabase` stub.

## Responsibilities

- Render each persona’s indicators into text “documents”
- Embed and store them in a vector store
- Provide similarity search and retriever interfaces
- Convert retrieved documents into a prompt-ready context string

## Public API

### `index_persona(persona: PersonaProfileModel) -> list[str]`

Adds a persona’s indicators to the vector store and returns vector store ids.

### `index_personas(personas: Iterable[PersonaProfileModel) -> list[str]`

Batch indexing helper.

### `search(query: str, k: int = 5) -> list[Document]`

Returns top-k similar documents.

### `as_retriever(k: int = 5) -> VectorStoreRetriever`

Returns a retriever wrapper for LangChain chains.

### `documents_to_context_prompt(documents: Iterable[Document]) -> str`

Renders a list of `Document` results to a single context string with headers, separated by `---`.

## Inputs/outputs

**Inputs**
- `embeddings: langchain_core.embeddings.Embeddings` (caller supplies the embedding model)
- personas: `PersonaProfileModel` objects (typed schema)

**Outputs**
- Retrieval: `langchain_core.documents.Document[]`
- Context: `str` suitable for injection into prompt builder

## Key dependencies / technologies

- `langchain_core.vectorstores.InMemoryVectorStore`
- `langchain_core.documents.Document`
- `langchain_core.embeddings.Embeddings`

## Notes / production hardening

- Swap `InMemoryVectorStore` with a persistent vector store for production.
- Add metadata filters to enforce persona scoping at retrieval time.
- Preserve `sources` (doc_id/pages) and emit citations in addition to context text.

