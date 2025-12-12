"""Authentication and authorization helpers for UI clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AuthService:
    """Very small in-memory auth registry for illustration purposes.
    It has to manage authentication and authorization, user access, permissions, and ensure only authorized users can interact
    with certain parts of the system"""

    _tokens: Dict[str, str] = field(default_factory=dict)

    def register(self, user: str, token: str) -> None:
        """Register a token for a given user."""

        self._tokens[user] = token

    def is_authorized(self, user: str, token: str) -> bool:
        """Validate whether the provided token matches the stored one."""

        return self._tokens.get(user) == token
