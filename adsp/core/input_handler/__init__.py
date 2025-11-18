"""Input normalization utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InputHandler:
    """Normalizes text or routes other modalities to preprocessors."""

    def normalize(self, text: str) -> str:
        return text.strip()
