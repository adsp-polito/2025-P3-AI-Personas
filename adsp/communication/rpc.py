"""RPC client placeholder used for synchronous service-to-service calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RPCClient:
    """Simple callable registry that mimics RPC semantics for local dev."""

    _resolver: Callable[[str], Callable]

    def call(self, service: str, payload: dict) -> Any:
        handler = self._resolver(service)
        return handler(payload)
