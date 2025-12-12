# Core: `ConversationMemory`

**Code**: `adsp/core/memory/__init__.py`

## Purpose

`ConversationMemory` stores recent chat history so the persona can behave consistently across turns.

## Responsibilities

- Append messages per persona
- Enforce a maximum history length
- Return history for context building (not yet wired into prompt construction)

## Public API

### `store(persona_id: str, message: dict) -> None`

Appends the message; evicts oldest entries once `max_items` is exceeded.

### `get_history(persona_id: str) -> list[dict]`

Returns a copy of the history list for the persona.

## Data model

- `_messages: DefaultDict[str, List[dict]]` (in-memory)
- `max_items: int` (default `10`)

## Key dependencies / technologies

- Python `dataclasses`
- `collections.defaultdict`

## Notes / production hardening

- Memory should be keyed by conversation/session (not only persona_id).
- Persist in a database for auditability and multi-instance deployments.
- Add summarization to fit token budgets.

