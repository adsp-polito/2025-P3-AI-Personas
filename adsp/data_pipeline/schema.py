"""Typed persona profile schema used across services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PersonaProfile:
    persona_id: str
    demographics: dict
    psychographics: dict
    behaviors: dict
    verbatims: List[str]
