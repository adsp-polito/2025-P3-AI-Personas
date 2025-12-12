# Application: `IngestionService`

**Code**: `adsp/app/ingestion_service.py`

## Purpose

`IngestionService` handles user-driven ingestion of files (PDFs/images/structured data). In the architecture, this is the application-layer entrypoint that persists uploads to object storage and triggers downstream processing.

## Responsibilities

- Accept uploaded file paths
- Persist their bytes into object storage
- (Planned) emit events / enqueue jobs for downstream data pipelines

## Public API

### `ingest_files(files: Iterable[pathlib.Path]) -> None`

**Inputs**
- `files`: iterable of local file paths (already available on the host)

**Output**
- None (side-effect: writes to object store)

## Internal logic (current)

For each `file_path`:
- Calls `adsp.storage.object_store.put(bucket, file_path)`

## Storage interactions

- Object storage shim: `adsp/storage/object_store.py`
  - `put(bucket: str, file_path: Path) -> None`

## Key dependencies / technologies

- Python `dataclasses`
- `pathlib.Path`
- In-memory object store shim (to be replaced by S3/GCS/Azure Blob)

## Notes / production hardening

- Add validation (file type, size limits, virus scanning).
- Replace `object_store` shim with S3-compatible client.
- Integrate with `EventBroker` / message queue to trigger:
  - persona extraction pipeline
  - RAG indexing pipeline

