"""Pipelines that turn PDFs/images/data into structured persona knowledge."""

from .ingestion import DocumentIngestionPipeline
from .schema import PersonaProfile, PersonaProfileModel

__all__ = [
    "DocumentIngestionPipeline",
    "PersonaProfile",
    "PersonaProfileModel",
]
