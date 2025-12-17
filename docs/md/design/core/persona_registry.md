# Core: `PersonaRegistry`

**Code**: `adsp/core/persona_registry/__init__.py`

## Purpose

`PersonaRegistry` stores persona metadata used by the Core layer for prompt construction and routing decisions.

## Responsibilities

- Maintain a catalog of persona metadata keyed by `persona_id`
- Provide read access for prompt building

## Public API

### `get(persona_id: str) -> dict`

Returns persona metadata dict, raises `KeyError` if missing.

### `upsert(persona_id: str, metadata: dict) -> None`

Stores/replaces metadata for the persona.

## Default persona

On initialization, the registry contains:
- `default`: `{ "preamble": "You are a Lavazza persona who is transparent and data-grounded." }`

## Key dependencies / technologies

- Python `dataclasses`
- In-memory `dict`

## Notes / integration

Production architecture typically sources persona definitions from the extracted persona profile JSON (`data/processed/personas/`) or a business database. A common pattern is:
- Load persona profiles at startup (or on demand) and `upsert` them into the registry.

