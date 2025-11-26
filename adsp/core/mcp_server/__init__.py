"""Selects external tools to enrich persona prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from adsp.core.mcp_server.tools import MCPClient


@dataclass
class MCPServer:
    """Coordinates MCP tool calls and caches their responses for reuse."""

    # mcp: MCPClient = MCPClient()
    mcp: MCPClient = field(default_factory=MCPClient())
    _cache: Dict[str, dict] = None

    def __post_init__(self) -> None:
        if self._cache is None:
            self._cache = {}

    def run(self, tool: str, payload: dict) -> dict:
        cache_key = f"{tool}:{tuple(sorted(payload.items()))}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self.mcp.request(tool, payload)
        return self._cache[cache_key]
