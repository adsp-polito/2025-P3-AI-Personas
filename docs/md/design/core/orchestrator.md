# Core: `Orchestrator`

**Code**: `adsp/core/orchestrator/__init__.py`

## Purpose

The Orchestrator is the Core layer’s coordinator. It turns a user query into a grounded, persona-voiced response by chaining preprocessing, retrieval, prompt construction, model routing, memory, and caching.

## Responsibilities

- Provide a single “handle query” entrypoint to the Application layer (`QAService`)
- Orchestrate:
  - input normalization
  - retrieval (RAG)
  - prompt construction
  - persona model routing
  - conversation memory writeback
  - response caching

## Public API

### `handle_query(persona_id: str, query: str) -> str`

**Inputs**
- `persona_id`: persona identifier used for retrieval + routing
- `query`: raw user question text (current implementation assumes text-only)

**Output**
- Persona response string

## Internal logic (current)

1. **Cache lookup**
   - `cache_key = f"{persona_id}:{session_id}:{query}"`
   - Return cached value if present (`CacheClient.get`)
2. **Normalize**
   - `normalized = InputHandler.normalize(query)`
3. **Retrieve context**
   - `retrieved = RAGPipeline.retrieve_with_metadata(persona_id=persona_id, query=normalized, k=top_k)`
4. **Filter for relevance**
   - Filter conversation history and retrieved context down to what is relevant for the current question
   - `filtered_history = ConversationContextFilter.filter_history(history, normalized)`
   - `filtered_retrieved = ConversationContextFilter.filter_retrieved(retrieved, normalized)`
5. **Build prompt**
   - `prompt = PromptBuilder.build(persona_id=persona_id, query=normalized, context=filtered_retrieved.context, history=filtered_history)`
6. **Dispatch to persona model**
   - `response = PersonaRouter.dispatch(persona_id=persona_id, prompt=prompt)`
7. **Persist memory**
   - `ConversationMemory.store(persona_id=persona_id, message={"query": query, "response": response})`
8. **Cache write**
   - `CacheClient.set(cache_key, response)`

## Inputs/outputs and extension points

The architecture (`docs/md/design.md`) calls for multimodal inputs (PDF/image). The orchestrator is the correct place to expand the request contract to:
- `attachments: list[{type, bytes|path|object_store_key}]`
- `session_id` or `conversation_id` (for memory)
- `requested_personas: list[str]` (virtual focus group fan-out)

## Key dependencies / technologies

- Python `dataclasses`
- Core subcomponents:
  - `adsp/core/input_handler/__init__.py` (`InputHandler`)
  - `adsp/core/context_filter.py` (`ConversationContextFilter`)
  - `adsp/core/rag/__init__.py` (`RAGPipeline`)
  - `adsp/core/prompt_builder/__init__.py` (`PromptBuilder`)
  - `adsp/core/ai_persona_router/__init__.py` (`PersonaRouter`)
  - `adsp/core/memory/__init__.py` (`ConversationMemory`)
- Communication:
  - `adsp/communication/cache.py` (`CacheClient`)

## Observability / monitoring (recommended)

Wire `MetricsCollector` to capture:
- cache hit/miss
- retrieval latency and top-k
- model latency and token usage
- error counts by stage

## Failure modes (current)

- Missing persona in `PersonaRegistry` → `KeyError` during prompt build
- Unconfigured model backend in the inference engine (stub today)
- Retrieval returns empty context (currently allowed; may degrade factuality)

## Relevance filtering (config)

Relevance filtering is enabled by default and can be configured via environment variables:

- `ADSP_CONTEXT_FILTER_ENABLED`: `true`/`false` (default: `true`)
- `ADSP_CONTEXT_FILTER_BACKEND`: `heuristic` (default) or `openai`
- `ADSP_CONTEXT_FILTER_MAX_HISTORY`: max history turns to include (default: `4`)
- `ADSP_CONTEXT_FILTER_MAX_BLOCKS`: max retrieved context blocks to include (default: `3`)
- `ADSP_CONTEXT_FILTER_MIN_COVERAGE`: minimum token coverage threshold (default: `0.2`)

Optional OpenAI-compatible backend settings (when `ADSP_CONTEXT_FILTER_BACKEND=openai`):

- `ADSP_CONTEXT_FILTER_BASE_URL` (defaults to `ADSP_LLM_BASE_URL` / `VLLM_BASE_URL`)
- `ADSP_CONTEXT_FILTER_MODEL` (defaults to `ADSP_LLM_MODEL` / `VLLM_MODEL`)
- `ADSP_CONTEXT_FILTER_API_KEY` (defaults to `ADSP_LLM_API_KEY` / `VLLM_API_KEY`)
