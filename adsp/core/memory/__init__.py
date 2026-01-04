"""Short-term memory store for conversations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, List, Optional, Tuple


@dataclass
class ConversationMemory:
    """Stores the last few interactions per persona."""

    max_items: int = 10
    _messages: DefaultDict[Tuple[str, str], List[dict]] = field(default_factory=lambda: defaultdict(list))

    @staticmethod
    def _key(persona_id: str, session_id: Optional[str]) -> Tuple[str, str]:
        return persona_id, session_id or "default"

    def store(self, persona_id: str, message: dict, *, session_id: Optional[str] = None) -> None:
        history = self._messages[self._key(persona_id, session_id)]
        history.append(message)
        if len(history) > self.max_items:
            history.pop(0)

    def get_history(self, persona_id: str, *, session_id: Optional[str] = None) -> List[dict]:
        return list(self._messages[self._key(persona_id, session_id)])
