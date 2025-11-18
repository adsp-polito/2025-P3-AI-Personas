"""Message-queue interface for asynchronous workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, DefaultDict, List
from collections import defaultdict


@dataclass
class EventBroker:
    """Publishes events to in-memory subscribers for now."""

    _subscribers: DefaultDict[str, List[Callable]] = field(default_factory=lambda: defaultdict(list))

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: dict) -> None:
        for handler in self._subscribers[topic]:
            handler(payload)
