"""Business logic relational database connector."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BusinessDatabase:
    """Stores persona definitions, auth data, and reporting metadata."""

    _tables: Dict[str, Dict] = field(default_factory=dict)

    def upsert(self, table: str, key: str, value: Dict) -> None:
        self._tables.setdefault(table, {})[key] = value

    def fetch(self, table: str, key: str) -> Dict:
        return self._tables.get(table, {}).get(key, {})
