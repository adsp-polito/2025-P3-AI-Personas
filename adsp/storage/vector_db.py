"""In-memory vector database stub."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, List


@dataclass
class VectorDatabase:
    """Stores persona documents and returns naive matches."""

    _documents: DefaultDict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    def upsert(self, persona_id: str, document: str) -> None:
        self._documents[persona_id].append(document)

    def search(self, persona_id: str, query: str) -> str:
        docs = self._documents[persona_id]
        if not docs:
            return ""
        return docs[-1]
