# Frontend: `ChatFrontend`

**Code**: `adsp/fe/chat_frontend.py`

## Purpose

`ChatFrontend` is a minimal UI-layer adapter that represents the “chat app” entrypoint in the system architecture. It wires authentication to the Q&A workflow.

## Responsibilities

- Validate that a user is authorized to chat.
- Forward an authorized message to the Q&A service.

## Public API

### `send_message(user: str, token: str, persona_id: str, message: str) -> str`

**Inputs**
- `user`: user identifier (string)
- `token`: auth token (string)
- `persona_id`: persona identifier to route the request
- `message`: user question / input

**Outputs**
- Returns `"Unauthorized"` if `AuthService.is_authorized()` fails
- Otherwise returns the string response from `QAService.ask()`

## Internal logic (current)

1. Calls `auth_service.is_authorized(user, token)`
2. If unauthorized, returns `"Unauthorized"`
3. If authorized, calls `qa_service.ask(persona_id=persona_id, query=message)` and returns its result

## Key dependencies / technologies

- Python `dataclasses`
- Application-layer services:
  - `adsp/app/auth_service.py` (`AuthService`)
  - `adsp/app/qa_service.py` (`QAService`)

## Notes / production hardening

- In production, this layer would typically be a real UI (e.g., Streamlit/React) calling an HTTP API, not in-process Python objects.
- Add attachment support (PDF/image) by extending the API to accept files and forwarding them to the orchestrator input handler.

