# Data Pipeline: `DocumentIngestionPipeline`

**Code**: `adsp/data_pipeline/ingestion.py`

## Purpose

`DocumentIngestionPipeline` is a minimal ingestion pipeline that persists uploaded files into object storage. It matches the first step of the platform’s background processing: turning UI uploads into durable artifacts for extraction/indexing.

## Responsibilities

- Accept a set of file paths
- Store each file in object storage under the configured bucket

## Public API

### `run(files: Iterable[pathlib.Path]) -> None`

**Inputs**
- `files`: iterable of local filesystem paths

**Outputs**
- None (side effect: object store write)

## Internal logic (current)

For each file:
- `adsp.storage.object_store.put(bucket, file_path)`

## Key dependencies / technologies

- Python `dataclasses`
- `pathlib.Path`
- `adsp/storage/object_store.py`

## Notes / production hardening

- In a real deployment, this pipeline would likely be invoked asynchronously from an event broker after `IngestionService` emits an event.
- Add metadata capture (doc_id, upload time, uploader, checksum) and store it in the business database.

