"""Handles user-driven ingestion requests for PDFs, images, and structured data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from adsp.storage import object_store


@dataclass
class IngestionService:
    """Uploads artifacts to object storage and queues preprocessing jobs."""

    bucket: str

    def ingest_files(self, files: Iterable[Path]) -> None:
        """Persist files to object storage and emit events for downstream pipelines."""

        for file_path in files:
            object_store.put(self.bucket, file_path)

    def ingest_bytes(self, filename: str, payload: bytes, *, bucket: Optional[str] = None) -> str:
        """Persist an in-memory payload to object storage.

        Returns the stored object key.
        """

        target_bucket = bucket or self.bucket
        object_store.put_bytes(target_bucket, filename, payload)
        return filename
