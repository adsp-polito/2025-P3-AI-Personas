"""REST API server for the Application layer.

This module is intentionally not imported from `adsp.app.__init__` so that the
core package remains usable even when FastAPI/uvicorn are not installed.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable, Optional

from loguru import logger

from adsp.app.api.routes import (
    register_auth_routes,
    register_chat_routes,
    register_group_routes,
    register_ingestion_routes,
    register_persona_routes,
    register_report_routes,
    register_survey_routes,
    register_system_routes,
)
from adsp.app.auth_service import AuthService
from adsp.app.ingestion_service import IngestionService
from adsp.app.qa_service import QAService
from adsp.app.report_service import ReportService
from adsp.config import PROCESSED_DATA_DIR


def _require_fastapi():
    try:
        from fastapi import FastAPI  # noqa: F401
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "FastAPI is required to run the REST API server. "
            "Install with `pip install fastapi uvicorn` (or `make install`)."
        ) from exc


class LazyQAService:
    """Lazily build the QA stack so API startup can return quickly."""

    def __init__(self, factory: Optional[Callable[[], QAService]] = None) -> None:
        self._factory = factory or QAService
        self._instance: Optional[QAService] = None
        self._error: Optional[Exception] = None
        self._lock = threading.Lock()
        self._status = "idle"

    @property
    def status(self) -> str:
        return self._status

    def warmup_async(self) -> None:
        if self._instance is not None or self._error is not None or self._status == "warming":
            return
        self._status = "warming"
        logger.info("API startup step 4/5: starting QA warmup thread")
        thread = threading.Thread(target=self._warmup, name="qa-service-warmup", daemon=True)
        thread.start()

    def _warmup(self) -> None:
        logger.info("QA warmup step 1/2: building QA service")
        try:
            self._get_instance()
        except Exception:
            logger.exception("QA service warmup failed")

    def _get_instance(self) -> QAService:
        instance = self._instance
        if instance is not None:
            return instance

        with self._lock:
            if self._instance is not None:
                return self._instance
            if self._error is not None:
                raise RuntimeError("QA service initialization failed") from self._error

            start = time.perf_counter()
            try:
                instance = self._factory()
            except Exception as exc:
                self._error = exc
                self._status = "error"
                raise RuntimeError("QA service initialization failed") from exc

            self._instance = instance
            self._status = "ready"
            logger.info(
                "QA warmup step 2/2: QA service ready in {:.2f}s",
                time.perf_counter() - start,
            )
            return instance

    def get_instance(self) -> QAService:
        return self._get_instance()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)


@dataclass
class AppServices:
    auth: AuthService
    qa: Any
    ingestion: IngestionService
    reports: ReportService
    surveys: Any
    groups: Any
    responses: Any


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


def _cors_middleware_options() -> dict[str, Any]:
    frontend_port = os.environ.get("ADSP_FE_PORT", "8501").strip() or "8501"
    allow_origins = _env_csv(
        "ADSP_API_CORS_ALLOW_ORIGINS",
        [
            f"http://localhost:{frontend_port}",
            f"http://127.0.0.1:{frontend_port}",
        ],
    )
    options: dict[str, Any] = {
        "allow_origins": allow_origins,
        "allow_credentials": _env_flag("ADSP_API_CORS_ALLOW_CREDENTIALS", False),
        "allow_methods": _env_csv("ADSP_API_CORS_ALLOW_METHODS", ["*"]),
        "allow_headers": _env_csv("ADSP_API_CORS_ALLOW_HEADERS", ["*"]),
    }
    expose_headers = _env_csv("ADSP_API_CORS_EXPOSE_HEADERS", [])
    if expose_headers:
        options["expose_headers"] = expose_headers

    allow_origin_regex = os.environ.get("ADSP_API_CORS_ALLOW_ORIGIN_REGEX", "").strip()
    if allow_origin_regex:
        options["allow_origin_regex"] = allow_origin_regex

    return options


def _default_docs_server_host() -> str:
    bind_host = os.environ.get("ADSP_API_HOST", "localhost").strip() or "localhost"
    if bind_host in {"0.0.0.0", "::", "[::]"}:
        bind_host = "localhost"

    bind_port = os.environ.get("ADSP_API_PORT", "8000").strip() or "8000"
    return f"{bind_host}:{bind_port}"


def _normalize_docs_server_base_path(raw: str) -> str:
    base_path = raw.strip()
    if not base_path:
        return ""
    if not base_path.startswith("/"):
        return f"/{base_path}"
    return base_path


def _openapi_servers() -> list[dict[str, Any]]:
    default_scheme = os.environ.get("ADSP_API_DOCS_SERVER_SCHEME", "http").strip().lower() or "http"
    if default_scheme not in {"http", "https"}:
        default_scheme = "http"

    default_host = os.environ.get("ADSP_API_DOCS_SERVER_HOST", _default_docs_server_host()).strip()
    if not default_host:
        default_host = _default_docs_server_host()

    default_base_path = _normalize_docs_server_base_path(
        os.environ.get("ADSP_API_DOCS_SERVER_BASE_PATH", "")
    )

    return [
        {
            "url": "/",
            "description": "Use the same origin as the loaded Swagger UI page.",
        },
        {
            "url": "{scheme}://{host}{base_path}",
            "description": "Editable API base URL for Swagger UI try-it-out requests.",
            "variables": {
                "scheme": {
                    "default": default_scheme,
                    "enum": ["http", "https"],
                    "description": "Protocol used by the API server.",
                },
                "host": {
                    "default": default_host,
                    "description": "API host and optional port, for example localhost:8000.",
                },
                "base_path": {
                    "default": default_base_path,
                    "description": "Optional URL prefix when the API is mounted behind a proxy.",
                },
            },
        },
    ]


def create_app() -> Any:
    """Create and configure the FastAPI application."""

    _require_fastapi()
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    title = os.environ.get("ADSP_API_TITLE", "Lavazza AI Personas API")
    version = os.environ.get("ADSP_API_VERSION", "0.1.0")
    debug = os.environ.get("ADSP_API_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}
    description = (
        "REST API for the Lavazza AI Personas application layer.\n\n"
        "Swagger UI: `/docs`\n"
        "OpenAPI JSON: `/openapi.json`"
    )

    app = FastAPI(
        title=title,
        version=version,
        description=description,
        servers=_openapi_servers(),
        debug=debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(CORSMiddleware, **_cors_middleware_options())

    @app.on_event("startup")
    def _startup() -> None:
        from adsp.core.survey.group_generator import GroupGenerator
        from adsp.core.survey.response_synthesizer import ResponseSynthesizer
        from adsp.core.survey.survey_manager import SurveyManager

        logger.info("API startup step 1/5: preparing application services")
        bucket = os.environ.get("ADSP_INGESTION_BUCKET", "uploads")
        reports_dir = Path(os.environ.get("ADSP_REPORTS_DIR", "reports/api"))
        reports_dir.mkdir(parents=True, exist_ok=True)
        surveys_dir = Path(os.environ.get("ADSP_SURVEYS_DIR", str(PROCESSED_DATA_DIR / "surveys")))
        logger.info("API startup step 2/5: reports directory ready at {}", reports_dir)
        qa = LazyQAService()
        logger.info("API startup step 3/5: creating auth, ingestion, and report services")
        app.state.services = AppServices(
            auth=AuthService(),
            qa=qa,
            ingestion=IngestionService(bucket=bucket),
            reports=ReportService(output_dir=reports_dir),
            surveys=SurveyManager(base_dir=surveys_dir),
            groups=GroupGenerator(base_dir=surveys_dir),
            responses=ResponseSynthesizer(base_dir=surveys_dir),
        )
        qa.warmup_async()
        logger.info("API startup step 5/5: server ready; health endpoint available; qa_status={}", qa.status)

    def get_services() -> AppServices:
        services = getattr(app.state, "services", None)
        if services is None:
            raise HTTPException(status_code=503, detail="Application services are not initialized")
        return services

    def get_qa_service(services: AppServices = Depends(get_services)) -> Any:
        try:
            qa = services.qa
            if isinstance(qa, LazyQAService):
                return qa.get_instance()
            return qa
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"QA service unavailable: {exc}") from exc

    def auth_required() -> bool:
        raw = os.environ.get("ADSP_REQUIRE_AUTH", "false").strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def authorize(
        services: AppServices = Depends(get_services),
        x_user: Optional[str] = Header(None, alias="X-User"),
        x_token: Optional[str] = Header(None, alias="X-Token"),
    ) -> None:
        if not auth_required():
            return
        if not x_user or not x_token:
            raise HTTPException(status_code=401, detail="Missing X-User/X-Token")
        if not services.auth.is_authorized(x_user, x_token):
            raise HTTPException(status_code=401, detail="Unauthorized")

    register_system_routes(app, version=version)
    register_auth_routes(app, get_services=get_services)
    register_persona_routes(app, get_qa_service=get_qa_service)
    register_chat_routes(app, get_qa_service=get_qa_service, authorize=authorize)
    register_ingestion_routes(app, get_services=get_services, authorize=authorize)
    register_report_routes(app, get_services=get_services, authorize=authorize)
    register_group_routes(app, get_services=get_services)
    register_survey_routes(app, get_services=get_services)

    return app


app = create_app()
