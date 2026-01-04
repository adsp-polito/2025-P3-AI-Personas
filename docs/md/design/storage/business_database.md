# Storage: `BusinessDatabase`

**Code**: `adsp/storage/business_db.py`

## Purpose

`BusinessDatabase` represents the system-of-record store for non-vector, structured data (users, auth records, persona definitions, reports metadata).

## Responsibilities

- Upsert structured records into named “tables”
- Fetch records by key

## Public API

### `upsert(table: str, key: str, value: dict) -> None`

Stores `value` under the given `(table, key)`.

### `fetch(table: str, key: str) -> dict`

Returns the stored record, or `{}` if missing.

## Data model

- `_tables: Dict[str, Dict]` (in-memory)

## Key dependencies / technologies

- Python `dataclasses`
- In-memory storage (`dict`)

## Notes / production hardening

Replace with a real DB (e.g., Postgres) and define explicit tables:
- `users`
- `sessions` / `tokens`
- `persona_definitions`
- `reports`
- `audit_logs` (especially important for explainability and compliance)

