# Storage: `object_store`

**Code**: `adsp/storage/object_store.py`

## Purpose

`object_store` is a minimal object storage shim used by ingestion and pipelines. In the architecture it corresponds to S3 (or equivalent).

## Responsibilities

- Store bytes for a file under a bucket/key
- Retrieve stored bytes by bucket/key

## Public API

### `put(bucket: str, file_path: pathlib.Path) -> None`

Reads bytes from `file_path` and stores them under `(bucket, file_path.name)`.

### `get(bucket: str, key: str) -> bytes`

Returns stored bytes for `(bucket, key)`.

## Data model

- `_STORE: Dict[str, Dict[str, bytes]]` (process-global in-memory)

## Key dependencies / technologies

- `pathlib.Path` for file IO
- In-memory dictionary storage

## Notes / production hardening

Replace with:
- AWS S3 / MinIO / GCS / Azure Blob client
- Content-addressable keys (hash-based) to avoid accidental overwrites
- Metadata (content type, original filename, uploaded_by, timestamps)
- Pre-signed URLs for frontend upload/download

