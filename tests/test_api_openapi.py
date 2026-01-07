"""
Smoke test to ensure that the public REST API contract is preserved.

This test checks that all expected OpenAPI paths are present.
It does NOT validate request/response schemas or business logic.
"""

import pytest


fastapi = pytest.importorskip("fastapi")
_ = fastapi  # silence unused in environments where it's installed


def test_openapi_paths_exist():
    from adsp.app.api_server import create_app

    app = create_app()
    schema = app.openapi()
    paths = schema.get("paths", {})

    # Minimal contract check: these endpoints must exist and be exposed
    # to avoid breaking clients when refactoring internal logic.
    expected = {
        "/health",
        "/v1/auth/register",
        "/v1/auth/validate",
        "/v1/personas",
        "/v1/personas/{persona_id}/profile",
        "/v1/personas/{persona_id}/system-prompt",
        "/v1/chat",
        "/v1/ingestion/upload",
        "/v1/reports/{persona_id}",
    }
    assert expected.issubset(set(paths.keys()))

