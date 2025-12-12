# Communication: `CacheClient`

**Code**: `adsp/communication/cache.py`

## Purpose

`CacheClient` provides a low-latency caching layer for frequently repeated computations (e.g., repeated persona answers for identical prompts).

## Responsibilities

- Store computed values by string key
- Retrieve cached values

## Public API

### `get(key: str) -> Any | None`

Returns the cached value if present; otherwise `None`.

### `set(key: str, value: Any) -> None`

Stores `value` under `key`.

## Data model

- `_entries: Dict[str, Any]` (in-memory)

## Current usage

Used by the Core orchestrator:
- `adsp/core/orchestrator/__init__.py` caches responses by `f"{persona_id}:{query}"`

## Key dependencies / technologies

- Python `dataclasses`
- In-memory `dict`

## Notes / production hardening

Replace the in-memory implementation with:
- Redis / Memcached
- Cache key strategy including:
  - persona version / adapter version
  - prompt template version
  - retrieval context hash (to prevent stale grounding)
- TTLs and cache invalidation policies

