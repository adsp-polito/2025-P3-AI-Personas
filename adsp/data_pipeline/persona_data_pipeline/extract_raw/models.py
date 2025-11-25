"""Shared data models for persona extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class PageImage:
    page_number: int  # 1-based
    image_path: Path
    width: int
    height: int


@dataclass
class PageExtractionResult:
    page_number: int
    raw_text: str
    parsed: Optional[dict]
    persona_id: Optional[str]
    patch: Dict[str, Any]
    error: Optional[str] = None
