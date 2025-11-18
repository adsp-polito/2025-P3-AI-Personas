"""Short-term memory store for conversations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, List


@dataclass
class ConversationMemory:
    """Stores the last few interactions per persona."""

    max_items: int = 10
    _messages: DefaultDict[str, List[dict]] = field(default_factory=lambda: defaultdict(list))

    def store(self, persona_id: str, message: dict) -> None:
        history = self._messages[persona_id]
        history.append(message)
        if len(history) > self.max_items:
            history.pop(0)

    def get_history(self, persona_id: str) -> List[dict]:
        return list(self._messages[persona_id])
