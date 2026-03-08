"""System/health API routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok", "version": "0.1.0", "qa_status": "ready"}}
    )

    status: str = Field(default="ok", description="Overall API health status.")
    version: str = Field(description="Application API version.")
    qa_status: str = Field(
        default="unknown",
        description="QA service warmup status. Expected values: idle, warming, ready, error.",
    )


def register_system_routes(app: Any, *, version: str) -> None:
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["system"],
        summary="Health Check",
        description="Returns API liveness and QA warmup status.",
    )
    def health() -> HealthResponse:
        services = getattr(app.state, "services", None)
        qa_status = getattr(getattr(services, "qa", None), "status", "unknown")
        return HealthResponse(version=version, qa_status=qa_status)
