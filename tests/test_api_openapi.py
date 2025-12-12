import pytest


fastapi = pytest.importorskip("fastapi")
_ = fastapi  # silence unused in environments where it's installed


def test_openapi_paths_exist():
    from adsp.app.api_server import create_app

    app = create_app()
    schema = app.openapi()
    paths = schema.get("paths", {})

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

