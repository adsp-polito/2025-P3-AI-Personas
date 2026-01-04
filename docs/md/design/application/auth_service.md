# Application: `AuthService`

**Code**: `adsp/app/auth_service.py`

## Purpose

`AuthService` provides a minimal authentication/authorization mechanism so UI clients can be gated before invoking persona workflows.

## Responsibilities

- Store user → token bindings
- Validate access with token equality

## Public API

### `register(user: str, token: str) -> None`

Stores the token for a user in an in-memory dictionary.

### `is_authorized(user: str, token: str) -> bool`

Returns `True` iff `token == stored_token_for_user`.

## Data model

- `_tokens: Dict[str, str]` (in-memory)

## Key dependencies / technologies

- Python `dataclasses`
- In-memory storage (`dict`)

## Notes / production hardening

The architecture in `docs/md/design.md` expects secure auth; this stub should be replaced with:

- Identity provider / SSO integration (OIDC/SAML)
- Token verification (JWT signature + expiration)
- Role-based access control (RBAC) for persona sets / documents
- Persistence in the business database (`adsp/storage/business_db.py` or a real DB)

