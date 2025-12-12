"""REST API server for the Application layer.

This module is intentionally not imported from `adsp.app.__init__` so that the
core package remains usable even when FastAPI/uvicorn are not installed.
"""

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from adsp.app.auth_service import AuthService
from adsp.app.ingestion_service import IngestionService
from adsp.app.qa_service import QAService
from adsp.app.report_service import ReportService
from adsp.core.prompt_builder.system_prompt import persona_to_system_prompt
from adsp.core.types import ChatRequest, ChatResponse
from adsp.data_pipeline.schema import PersonaProfileModel


def _require_fastapi():
    try:
        from fastapi import FastAPI  # noqa: F401
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "FastAPI is required to run the REST API server. "
            "Install with `pip install fastapi uvicorn` (or `make install`)."
        ) from exc


@dataclass
class AppServices:
    auth: AuthService
    qa: QAService
    ingestion: IngestionService
    reports: ReportService


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class AuthRegisterRequest(BaseModel):
    user: str
    token: str


class AuthValidateRequest(BaseModel):
    user: str
    token: str


class AuthValidateResponse(BaseModel):
    authorized: bool


class PersonaSummary(BaseModel):
    persona_id: str
    persona_name: Optional[str] = None
    summary_bio: Optional[str] = None


class PersonasListResponse(BaseModel):
    personas: List[PersonaSummary] = Field(default_factory=list)


class SystemPromptResponse(BaseModel):
    system_prompt: str


class ChatResponseEnvelope(BaseModel):
    response: ChatResponse


class UploadRequest(BaseModel):
    filename: str
    content_base64: str
    bucket: Optional[str] = None


class UploadResponse(BaseModel):
    bucket: str
    key: str
    size_bytes: int


class ReportGenerateRequest(BaseModel):
    insights: Dict[str, Any] = Field(default_factory=dict)


class ReportGenerateResponse(BaseModel):
    path: str


def create_app() -> Any:
    """Create and configure the FastAPI application."""

    _require_fastapi()
    from fastapi import Depends, FastAPI, Header, HTTPException, Request

    title = os.environ.get("ADSP_API_TITLE", "Lavazza AI Personas API")
    version = os.environ.get("ADSP_API_VERSION", "0.1.0")
    description = (
        "REST API for the Lavazza AI Personas application layer.\n\n"
        "Swagger UI: `/docs`\n"
        "OpenAPI JSON: `/openapi.json`"
    )

    app = FastAPI(
        title=title,
        version=version,
        description=description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.on_event("startup")
    def _startup() -> None:
        bucket = os.environ.get("ADSP_INGESTION_BUCKET", "uploads")
        reports_dir = Path(os.environ.get("ADSP_REPORTS_DIR", "reports/api"))
        reports_dir.mkdir(parents=True, exist_ok=True)
        app.state.services = AppServices(
            auth=AuthService(),
            qa=QAService(),
            ingestion=IngestionService(bucket=bucket),
            reports=ReportService(output_dir=reports_dir),
        )
        logger.info("API server started")

    def get_services(request: Request) -> AppServices:
        return request.app.state.services

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

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(version=version)

    @app.post("/v1/auth/register", tags=["auth"])
    def register_auth(payload: AuthRegisterRequest, services: AppServices = Depends(get_services)) -> Dict[str, str]:
        services.auth.register(payload.user, payload.token)
        return {"status": "ok"}

    @app.post("/v1/auth/validate", response_model=AuthValidateResponse, tags=["auth"])
    def validate_auth(
        payload: AuthValidateRequest, services: AppServices = Depends(get_services)
    ) -> AuthValidateResponse:
        return AuthValidateResponse(authorized=services.auth.is_authorized(payload.user, payload.token))

    @app.get("/v1/personas", response_model=PersonasListResponse, tags=["personas"])
    def list_personas(services: AppServices = Depends(get_services)) -> PersonasListResponse:
        registry = services.qa.orchestrator.prompt_builder.registry
        items: List[PersonaSummary] = []
        for persona_id in registry.list_personas():
            persona = registry.get(persona_id)
            if isinstance(persona, PersonaProfileModel):
                items.append(
                    PersonaSummary(
                        persona_id=persona_id,
                        persona_name=persona.persona_name,
                        summary_bio=persona.summary_bio,
                    )
                )
            elif isinstance(persona, dict):
                items.append(PersonaSummary(persona_id=persona_id, persona_name=persona.get("persona_name")))
            else:
                items.append(PersonaSummary(persona_id=persona_id))
        return PersonasListResponse(personas=items)

    @app.get("/v1/personas/{persona_id}/profile", response_model=PersonaProfileModel, tags=["personas"])
    def get_persona_profile(persona_id: str, services: AppServices = Depends(get_services)) -> PersonaProfileModel:
        registry = services.qa.orchestrator.prompt_builder.registry
        persona = registry.get(persona_id)
        if not isinstance(persona, PersonaProfileModel):
            raise HTTPException(status_code=404, detail="Persona profile not available")
        return persona

    @app.get("/v1/personas/{persona_id}/system-prompt", response_model=SystemPromptResponse, tags=["personas"])
    def get_system_prompt(persona_id: str, services: AppServices = Depends(get_services)) -> SystemPromptResponse:
        registry = services.qa.orchestrator.prompt_builder.registry
        persona = registry.get(persona_id)
        if isinstance(persona, PersonaProfileModel):
            return SystemPromptResponse(system_prompt=persona_to_system_prompt(persona))
        if isinstance(persona, dict):
            return SystemPromptResponse(system_prompt=str(persona.get("preamble", "You are an AI persona.")))
        raise HTTPException(status_code=404, detail="Persona not found")

    @app.post("/v1/chat", response_model=ChatResponseEnvelope, tags=["chat"], dependencies=[Depends(authorize)])
    def chat(payload: ChatRequest, services: AppServices = Depends(get_services)) -> ChatResponseEnvelope:
        response = services.qa.orchestrator.handle(payload)
        return ChatResponseEnvelope(response=response)

    @app.post(
        "/v1/ingestion/upload",
        response_model=UploadResponse,
        tags=["ingestion"],
        dependencies=[Depends(authorize)],
    )
    def upload(payload: UploadRequest, services: AppServices = Depends(get_services)) -> UploadResponse:
        try:
            raw = base64.b64decode(payload.content_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {exc}") from exc

        bucket = payload.bucket or services.ingestion.bucket
        key = payload.filename
        services.ingestion.ingest_bytes(key, raw, bucket=bucket)
        return UploadResponse(bucket=bucket, key=key, size_bytes=len(raw))

    @app.post(
        "/v1/reports/{persona_id}",
        response_model=ReportGenerateResponse,
        tags=["reports"],
        dependencies=[Depends(authorize)],
    )
    def generate_report(
        persona_id: str,
        payload: ReportGenerateRequest,
        services: AppServices = Depends(get_services),
    ) -> ReportGenerateResponse:
        report_path = services.reports.generate(persona_id=persona_id, insights=payload.insights)
        return ReportGenerateResponse(path=str(report_path))

    return app


app = create_app()
