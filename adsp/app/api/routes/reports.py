"""Reporting API routes."""

from __future__ import annotations

from typing import Any, Callable, Dict

from pydantic import BaseModel, ConfigDict, Field


class ReportGenerateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "insights": {
                    "top_drivers": ["taste", "price", "brand trust"],
                    "summary": "Customer segment values consistency and practical value.",
                }
            }
        }
    )

    insights: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary insights payload to render into a report markdown file.",
    )


class ReportGenerateResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"path": "reports/api/curious-connoisseurs_report.md"}}
    )

    path: str = Field(description="Absolute or relative path of generated report file.")


def register_report_routes(
    app: Any,
    *,
    get_services: Callable[..., Any],
    authorize: Callable[..., Any],
) -> None:
    from fastapi import Depends, Path

    @app.post(
        "/v1/reports/{persona_id}",
        response_model=ReportGenerateResponse,
        tags=["reports"],
        dependencies=[Depends(authorize)],
        summary="Generate Persona Report",
        description="Writes a markdown report for the selected persona using provided insights.",
    )
    def generate_report(
        payload: ReportGenerateRequest,
        persona_id: str = Path(description="Persona identifier used to name the report file."),
        services: Any = Depends(get_services),
    ) -> ReportGenerateResponse:
        report_path = services.reports.generate(persona_id=persona_id, insights=payload.insights)
        return ReportGenerateResponse(path=str(report_path))
