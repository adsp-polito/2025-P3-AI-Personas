"""Caching abstraction for low-latency persona responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CacheClient:
    """A naive in-memory cache placeholder. Replace with Redis/Memcached."""

    _entries: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Optional[Any]:
        return self._entries.get(key)

    def set(self, key: str, value: Any) -> None:
        self._entries[key] = value
