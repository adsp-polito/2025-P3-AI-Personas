"""Pipelines that turn PDFs/images/data into structured persona knowledge."""

from .ingestion import DocumentIngestionPipeline
from .schema import PersonaProfile

__all__ = [
    "DocumentIngestionPipeline",
    "PersonaProfile",
]
