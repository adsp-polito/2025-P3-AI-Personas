# Application: `PersonaConfigurationService`

**Code**: `adsp/app/persona_config.py`

## Purpose

`PersonaConfigurationService` is the application-layer interface for creating and listing personas available to the system.

## Responsibilities

- Register persona definitions (metadata + behavioral configuration)
- List available personas
- Retrieve persona definitions by id

## Public API

### `register_persona(persona_id: str, definition: dict) -> None`

Stores a persona definition in an in-memory dictionary.

### `list_personas() -> list[str]`

Returns sorted persona IDs.

### `get_persona(persona_id: str) -> dict`

Returns the persona definition; raises `KeyError` if missing.

## Data model

- `_personas: Dict[str, Dict]` (in-memory)

## Key dependencies / technologies

- Python `dataclasses`
- In-memory storage (`dict`)

## Notes / integration

- The Core layer has its own `PersonaRegistry` (`adsp/core/persona_registry/__init__.py`). In production you typically unify these:
  - Application layer writes persona definitions to a persistent store (business DB).
  - Core layer loads and caches them for prompt construction + routing.

