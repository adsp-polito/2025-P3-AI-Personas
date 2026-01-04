# Application: `QAService`

**Code**: `adsp/app/qa_service.py`

## Purpose

`QAService` is the UI-facing entrypoint for interactive persona Q&A. It forwards queries into the Core layer’s orchestrator.

## Responsibilities

- Receive `(persona_id, query)` from the frontend
- Invoke the Core orchestration pipeline and return the final text response

## Public API

### `ask(persona_id: str, query: str) -> str`

**Inputs**
- `persona_id`: persona to use for voice/routing
- `query`: the user question

**Output**
- `str` response (persona answer)

## Internal logic (current)

1. Creates a new `core.orchestrator.Orchestrator()`
2. Calls `Orchestrator.handle_query(persona_id=persona_id, query=query)`

## Key dependencies / technologies

- `adsp/core/orchestrator/__init__.py` (`Orchestrator`)
- Python `dataclasses`

## Notes / production hardening

- The current implementation instantiates a new orchestrator per call; in production you would inject a long-lived orchestrator with configured dependencies (vector DB client, persona registry, cache, metrics).
- Add request metadata:
  - `session_id` (for memory)
  - `attachments` (PDF/image)
  - `requested_personas[]` (for “virtual focus group” multi-persona fan-out)

