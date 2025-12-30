"""Synonym configuration for evaluation matching."""

from __future__ import annotations

from typing import Dict

# Map common variants to a canonical token for label matching.
WORD_SYNONYMS: Dict[str, str] = {
    "cap": "capsule",
    "caps": "capsule",
    "capsule": "capsule",
    "capsules": "capsule",
}
