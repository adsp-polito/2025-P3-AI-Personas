# Communication: `RPCClient`

**Code**: `adsp/communication/rpc.py`

## Purpose

`RPCClient` is a placeholder for synchronous service-to-service calls (RPC/gRPC/HTTP) inside the platform.

## Responsibilities

- Route a `(service, payload)` request to a resolved handler
- Return the handler’s response

## Public API

### `call(service: str, payload: dict) -> Any`

**Inputs**
- `service`: logical service name
- `payload`: request payload

**Output**
- Any response returned by the resolved handler

## Internal logic (current)

1. Calls `_resolver(service)` to get a callable handler
2. Calls `handler(payload)` and returns the result

## Key dependencies / technologies

- Python `dataclasses`
- Callable injection for `_resolver`

## Notes / production hardening

Replace with:
- HTTP (FastAPI) or gRPC client stubs
- Typed request/response models (Pydantic/Protobuf)
- Timeouts, retries, tracing propagation

