# Core: `MCPClient`

**Code**: `adsp/core/mcp_server/tools/mcp_client.py`

## Purpose

`MCPClient` is the client-side interface to request tool execution. Today it is a mock that echoes the request.

## Responsibilities

- Provide a simple `request(tool, payload)` function
- (Planned) communicate with external tool servers/processes

## Public API

### `request(tool: str, payload: dict) -> dict`

Returns `{ "tool": tool, "payload": payload }`.

## Key dependencies / technologies

- Python `dataclasses`

## Notes / production hardening

Replace with:
- MCP-compatible transport (HTTP/websocket/stdin-stdio)
- Tool registry and authentication
- Structured tool schemas for safe calling

