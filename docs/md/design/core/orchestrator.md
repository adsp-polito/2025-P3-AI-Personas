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
   - `cache_key = f"{persona_id}:{query}"`
   - Return cached value if present (`CacheClient.get`)
2. **Normalize**
   - `normalized = InputHandler.normalize(query)`
3. **Retrieve context**
   - `context = RAGPipeline.retrieve(persona_id=persona_id, query=normalized)`
4. **Build prompt**
   - `prompt = PromptBuilder.build(persona_id=persona_id, query=normalized, context=context)`
5. **Dispatch to persona model**
   - `response = PersonaRouter.dispatch(persona_id=persona_id, prompt=prompt)`
6. **Persist memory**
   - `ConversationMemory.store(persona_id=persona_id, message={"query": query, "response": response})`
7. **Cache write**
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

