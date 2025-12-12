# Core: `MCPServer`

**Code**: `adsp/core/mcp_server/__init__.py`, `adsp/core/mcp_server/tools/mcp_client.py`

## Purpose

`MCPServer` is the Core component responsible for calling external “tools” via a Model Context Protocol-style interface and caching their responses.

In the architecture (`docs/md/design.md`), tool calls are used to enrich the model context with:
- web search
- database queries
- external APIs
- utilities (calculators, simulators, etc.)

## Responsibilities

- Provide `run(tool, payload)` interface
- Cache tool responses by a deterministic key

## Public API

### `run(tool: str, payload: dict) -> dict`

**Inputs**
- `tool`: tool name (string identifier)
- `payload`: tool request payload

**Output**
- Tool response dict (cached for identical requests)

## Internal logic (current)

1. Creates `cache_key = f"{tool}:{tuple(sorted(payload.items()))}"`
2. If `cache_key` not present, calls `MCPClient.request(tool, payload)` and stores the result
3. Returns cached result

## Key dependencies / technologies

- Python `dataclasses`
- Simple in-process caching (`dict`)

## Notes / production hardening

- Deterministic keying should handle nested payloads and non-hashable types (current implementation assumes flat payload).
- Add timeouts, retries, rate limiting.
- Persist tool-call traces for explainability (“why did the model say this?”).

