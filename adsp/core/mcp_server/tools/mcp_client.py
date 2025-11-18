"""Mock MCP client that would normally communicate with external tools."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MCPClient:
    """Provides a very small interface to request external context."""

    def request(self, tool: str, payload: dict) -> dict:
        return {"tool": tool, "payload": payload}
