"""Utility helpers for persona extraction."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import List


def strip_json_markdown(text: str) -> str:
    """Extract JSON content from possible markdown fences."""
    if "```" not in text:
        return text.strip()
    blocks: List[str] = []
    for part in text.split("```"):
        cleaned = part.strip()
        if not cleaned:
            continue
        if cleaned.startswith("json"):
            cleaned = cleaned[len("json") :].strip()
        blocks.append(cleaned)
    for block in blocks:
        if block.startswith("{") or block.startswith("["):
            return block
    if blocks:
        return max(blocks, key=len)
    return text.strip()


def encode_image_base64(image_path: Path) -> str:
    with image_path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
