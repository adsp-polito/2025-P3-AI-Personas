# Wiring LangChain RAG into the Orchestrator

The Core `RAGPipeline` currently delegates to an in-memory stub `VectorDatabase` and returns only a context string. This guide describes how to wire the LangChain-based indicator retriever into runtime query handling.

## Target behavior

- Index persona indicators into a vector store at startup (or after extraction).
- At query time:
  - retrieve top-k relevant indicator documents
  - format them into a context string for the prompt
  - return structured citations (doc_id/pages) for explainability

## Building the index

Inputs:
- persona profiles: `data/processed/personas/individual/*.json`
- schema loader: `adsp.data_pipeline.schema.load_persona_profile`

Retriever:
- `adsp.data_pipeline.persona_data_pipeline.rag.PersonaIndicatorRAG`

Embeddings:
- Provide any `langchain_core.embeddings.Embeddings` implementation.
- This repo includes `langchain-huggingface` + `sentence-transformers` in `requirements.txt`.

## Query-time retrieval

1. `docs = indicator_rag.search(query, k=5)`
2. `context = documents_to_context_prompt(docs)`
3. Build prompt: `PromptBuilder.build(..., context=context)`

## Integrating with `Orchestrator`

Recommended approach:
- Replace `RAGPipeline.retrieve()` to return both:
  - `context: str`
  - `citations: list[dict]` (derived from `Document.metadata` + `sources`)
- Update `Orchestrator.handle_query()` to return a structured response including citations.

If you keep the current string-only API:
- You can still return `context` built from `documents_to_context_prompt()`, but citations will be lost unless added elsewhere.

## Related docs

- `docs/md/design/data_pipeline/indicator_rag.md`
- `docs/md/design/core/rag_pipeline.md`
- `docs/md/design/core/explanation.md`

