# Core: Explanation Module (Design)

**Architecture reference**: `docs/md/design.md` lists an “Explanation” module for transparency and traceability.

## Purpose

The Explanation module provides user-visible justification for outputs:
- what evidence was retrieved (citations)
- what persona rules were applied
- what tool calls (MCP) were made
- why the system refused / said “not enough data” (non-hallucination)

## Recommended API

Expose an explanation payload alongside the answer:

```json
{
  "answer": "string",
  "citations": [
    { "doc_id": "string", "pages": [1, 2], "snippet": "string", "score": 0.0 }
  ],
  "persona": { "persona_id": "string", "version": "string?" },
  "retrieval": { "k": 5, "source": "vector_db|indicator_rag", "query": "string" },
  "tool_calls": [ { "tool": "string", "payload": {}, "result_summary": "string" } ],
  "safety": { "refusal": false, "not_enough_data": false }
}
```

## Integration points

- `Orchestrator.handle_query()` should return a structured response (not only a string) so explanation can be returned to the UI.
- `RAGPipeline` should return structured citations (doc/page) rather than only a context string.
- `MCPServer` should log tool calls and cache keys.

## Key technologies (recommended)

- Typed models: Pydantic
- Logging/tracing: OpenTelemetry
- UI rendering: expandable “Evidence” panel showing citations and tool outputs

