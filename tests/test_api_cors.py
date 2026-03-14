"""CORS configuration checks for the REST API server."""

import pytest as pytest

fastapi = pytest.importorskip("fastapi")
unused_fastapi = fastapi


def _build_app():
    from adsp.app.api_server import create_app

    return create_app()


def _cors_middleware(app):
    from fastapi.middleware.cors import CORSMiddleware

    return next((entry for entry in app.user_middleware if entry.cls is CORSMiddleware), None)


def test_app_enables_cors_for_local_frontend(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ADSP_FE_PORT", raising=False)
    monkeypatch.delenv("ADSP_API_CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.delenv("ADSP_API_CORS_ALLOW_METHODS", raising=False)
    monkeypatch.delenv("ADSP_API_CORS_ALLOW_HEADERS", raising=False)
    monkeypatch.delenv("ADSP_API_CORS_EXPOSE_HEADERS", raising=False)
    monkeypatch.delenv("ADSP_API_CORS_ALLOW_CREDENTIALS", raising=False)
    monkeypatch.delenv("ADSP_API_CORS_ALLOW_ORIGIN_REGEX", raising=False)

    middleware = _cors_middleware(_build_app())
    assert middleware is not None
    assert middleware.kwargs["allow_origins"] == [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    assert middleware.kwargs["allow_methods"] == ["*"]
    assert middleware.kwargs["allow_headers"] == ["*"]
    assert middleware.kwargs["allow_credentials"] is False


def test_app_uses_env_for_cors_configuration(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ADSP_FE_PORT", "3000")
    monkeypatch.setenv("ADSP_API_CORS_ALLOW_ORIGINS", "https://app.example.com, https://admin.example.com")
    monkeypatch.setenv("ADSP_API_CORS_ALLOW_METHODS", "GET,POST,OPTIONS")
    monkeypatch.setenv("ADSP_API_CORS_ALLOW_HEADERS", "Authorization,Content-Type,X-User,X-Token")
    monkeypatch.setenv("ADSP_API_CORS_EXPOSE_HEADERS", "X-Request-Id")
    monkeypatch.setenv("ADSP_API_CORS_ALLOW_CREDENTIALS", "true")
    monkeypatch.setenv("ADSP_API_CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.example\.com")

    middleware = _cors_middleware(_build_app())
    assert middleware is not None
    assert middleware.kwargs["allow_origins"] == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert middleware.kwargs["allow_methods"] == ["GET", "POST", "OPTIONS"]
    assert middleware.kwargs["allow_headers"] == [
        "Authorization",
        "Content-Type",
        "X-User",
        "X-Token",
    ]
    assert middleware.kwargs["expose_headers"] == ["X-Request-Id"]
    assert middleware.kwargs["allow_credentials"] is True
    assert middleware.kwargs["allow_origin_regex"] == r"https://.*\.example\.com"
