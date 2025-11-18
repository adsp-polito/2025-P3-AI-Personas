"""Pipelines for turning uploaded data into machine-readable assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from adsp.storage.object_store import put


@dataclass
class DocumentIngestionPipeline:
    bucket: str

    def run(self, files: Iterable[Path]) -> None:
        for file_path in files:
            put(self.bucket, file_path)
