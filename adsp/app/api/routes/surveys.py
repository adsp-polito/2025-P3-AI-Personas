"""Survey simulation API routes."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SurveyCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "survey_id": "coffee-pref-2026-q1",
                "title": "Coffee Preference Survey",
                "description": "Capture product and value preferences for coffee buyers.",
                "questions": [
                    {
                        "question_id": "q1",
                        "text": "Which product claim matters most?",
                        "type": "multiple_choice",
                        "options": ["Great taste", "Affordable price", "Sustainable sourcing"],
                    },
                    {
                        "question_id": "q2",
                        "text": "How likely are you to try a new blend?",
                        "type": "rating",
                        "metadata": {"scale": "1-5"},
                    },
                ],
            }
        }
    )

    survey_id: Optional[str] = Field(
        default=None,
        description="Optional survey identifier. If omitted, one is generated automatically.",
    )
    title: str = Field(description="Survey display title.")
    description: str = Field(default="", description="Survey description or objective.")
    questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Question list. Each item should include at least `question_id`, `text`, and `type` "
            "(multiple_choice, rating, open_ended)."
        ),
    )


class SurveyDetailResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "survey_id": "coffee-pref-2026-q1",
                "title": "Coffee Preference Survey",
                "description": "Capture product and value preferences for coffee buyers.",
                "created_at": "2026-03-08T15:30:12.002812+00:00",
                "questions": [
                    {
                        "question_id": "q1",
                        "text": "Which product claim matters most?",
                        "type": "multiple_choice",
                        "options": ["Great taste", "Affordable price", "Sustainable sourcing"],
                    }
                ],
                "simulations": [],
            }
        }
    )

    survey_id: str = Field(description="Survey identifier.")
    title: str = Field(description="Survey title.")
    description: str = Field(default="", description="Survey description.")
    created_at: str = Field(description="Creation timestamp in ISO-8601 format.")
    questions: List[Dict[str, Any]] = Field(default_factory=list, description="Persisted survey question list.")
    simulations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Simulation runs with metadata and progress for this survey.",
    )


class PagingMeta(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 45,
                "total_pages": 3,
            }
        }
    )

    page: int = Field(description="Current page number (1-based).")
    page_size: int = Field(description="Maximum number of items per page.")
    total_items: int = Field(description="Total number of available items.")
    total_pages: int = Field(description="Total number of pages at the selected page size.")


class SurveysListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "survey_id": "coffee-pref-2026-q1",
                        "title": "Coffee Preference Survey",
                        "description": "Capture product and value preferences for coffee buyers.",
                        "created_at": "2026-03-08T15:30:12.002812+00:00",
                        "questions": [],
                    }
                ],
                "paging": {"page": 1, "page_size": 20, "total_items": 45, "total_pages": 3},
            }
        }
    )

    items: List[SurveyDetailResponse] = Field(default_factory=list, description="Paged survey list.")
    paging: PagingMeta = Field(description="Paging metadata for the survey list.")


class SimulateSurveyRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"group_id": "group-ab12cd34"}}
    )

    group_id: str = Field(description="Respondent group identifier used for simulation.")
    # batch_size: int = Field(default=10, description="Requested batch size for response generation.")
    # format: str = Field(
    #     default="json",
    #     description="Desired output format hint (current export route supports csv/json).",
    # )


class SimulateSurveyResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "simulation_id": "sim-1234abcd",
                "status": "processing",
                "total_respondents": 40,
                "progress": {"completed": 0, "pending": 40},
                "estimated_time_minutes": 1,
            }
        }
    )

    simulation_id: str = Field(description="Simulation identifier.")
    status: str = Field(description="Simulation status.")
    total_respondents: int = Field(description="Total respondents processed for this simulation.")
    progress: Dict[str, int] = Field(default_factory=dict, description="Completion counters for simulation progress.")
    estimated_time_minutes: int = Field(description="Estimated completion time in minutes.")


class SimulationResponseAnswerDetail(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q1",
                "question_text": "Which product claim matters most?",
                "answer_type": "choice",
                "value": "Great taste",
                "confidence": 0.92,
                "reasoning": "Taste is the main purchase driver for this respondent.",
            }
        }
    )

    question_id: str = Field(description="Question identifier.")
    question_text: str = Field(description="Question text copied from the survey definition.")
    answer_type: str = Field(description="Answer type for this question.")
    value: Any = Field(description="Raw answer value.")
    confidence: float = Field(description="Confidence score produced during synthesis.")
    reasoning: Optional[str] = Field(default=None, description="Optional answer reasoning text.")


class SimulationResponseDetail(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response_id": "resp-1234abcd",
                "respondent_id": "group-1-resp-00001",
                "respondent_name": "Alice Example",
                "persona_id": "curious-connoisseurs",
                "completed_at": "2026-03-14T20:15:02+00:00",
                "answers": [],
            }
        }
    )

    response_id: str = Field(description="Response identifier.")
    respondent_id: str = Field(description="Respondent identifier.")
    respondent_name: Optional[str] = Field(default=None, description="Respondent display name when available.")
    persona_id: Optional[str] = Field(default=None, description="Persona identifier for the respondent.")
    completed_at: str = Field(description="Completion timestamp in ISO-8601 format.")
    answers: List[SimulationResponseAnswerDetail] = Field(
        default_factory=list,
        description="Question-level answers for this response.",
    )


class SimulationResponseDetailsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "survey_id": "coffee-pref-2026-q1",
                "simulation_id": "sim-1234abcd",
                "group_id": "group-ab12cd34",
                "total_responses": 40,
                "responses": [],
            }
        }
    )

    survey_id: str = Field(description="Survey identifier.")
    simulation_id: str = Field(description="Simulation identifier.")
    group_id: str = Field(description="Respondent group used for the simulation.")
    total_responses: int = Field(description="Total number of detailed responses returned.")
    responses: List[SimulationResponseDetail] = Field(
        default_factory=list,
        description="Detailed simulated responses enriched with respondent and question metadata.",
    )


class DistributionEntry(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"value": "Great taste", "count": 18, "percentage": 0.45}}
    )

    value: str = Field(description="Answer value bucket.")
    count: int = Field(description="Number of answers in this bucket.")
    percentage: float = Field(description="Bucket ratio over non-empty answers for the question.")


class SurveyQuestionStatistics(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q1",
                "text": "Which product claim matters most?",
                "type": "multiple_choice",
                "answered_count": 40,
                "response_rate": 1.0,
                "choice_distribution": [
                    {"value": "Great taste", "count": 18, "percentage": 0.45},
                    {"value": "Affordable price", "count": 12, "percentage": 0.3},
                    {"value": "Sustainable sourcing", "count": 10, "percentage": 0.25},
                ],
                "rating_distribution": [],
                "rating_average": None,
                "rating_min": None,
                "rating_max": None,
                "text_response_count": 0,
                "sample_text_responses": [],
            }
        }
    )

    question_id: str = Field(description="Question identifier.")
    text: str = Field(description="Question text.")
    type: str = Field(description="Question type.")
    answered_count: int = Field(description="Count of non-empty answers for this question.")
    response_rate: float = Field(description="Answer rate over `total_respondents`.")
    choice_distribution: List[DistributionEntry] = Field(
        default_factory=list,
        description="Choice distribution for `multiple_choice` questions.",
    )
    rating_distribution: List[DistributionEntry] = Field(
        default_factory=list,
        description="Rating distribution for `rating` questions.",
    )
    rating_average: Optional[float] = Field(default=None, description="Average rating value when applicable.")
    rating_min: Optional[float] = Field(default=None, description="Minimum rating value when applicable.")
    rating_max: Optional[float] = Field(default=None, description="Maximum rating value when applicable.")
    text_response_count: int = Field(description="Count of non-empty text answers for `open_ended` questions.")
    sample_text_responses: List[str] = Field(
        default_factory=list,
        description="Up to three sample text responses for `open_ended` questions.",
    )


class SurveyStatisticsResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "survey_id": "coffee-pref-2026-q1",
                "simulation_id": "sim-1234abcd",
                "total_respondents": 40,
                "total_responses": 40,
                "computed_at": "2026-03-08T18:00:00+00:00",
                "questions": [],
            }
        }
    )

    survey_id: str = Field(description="Survey identifier.")
    simulation_id: str = Field(description="Simulation identifier used to compute stats.")
    total_respondents: int = Field(description="Total respondents in the selected simulation.")
    total_responses: int = Field(description="Total response documents processed.")
    computed_at: str = Field(description="Statistic computation timestamp in ISO-8601 format.")
    questions: List[SurveyQuestionStatistics] = Field(
        default_factory=list,
        description="Question-level response statistics for the selected simulation.",
    )


def _model_payload(payload: BaseModel) -> Dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_none=True)
    return payload.dict(exclude_none=True)


def _to_iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _survey_response_payload(
    survey: Any,
    *,
    simulations: Optional[List[Dict[str, Any]]] = None,
) -> SurveyDetailResponse:
    payload = survey.model_dump(mode="json") if hasattr(survey, "model_dump") else survey.dict()
    return SurveyDetailResponse(
        survey_id=str(payload.get("survey_id", "")),
        title=str(payload.get("title", "")),
        description=str(payload.get("description", "")),
        created_at=_to_iso(payload.get("created_at")),
        questions=payload.get("questions", []) if isinstance(payload.get("questions"), list) else [],
        simulations=simulations or [],
    )


def _simulation_payload(simulation: Any, *, statistics_ready: bool) -> Dict[str, Any]:
    return {
        "simulation_id": simulation.simulation_id,
        "group_id": simulation.group_id,
        "status": simulation.status,
        "started_at": _to_iso(simulation.started_at),
        "completed_at": _to_iso(simulation.completed_at) if simulation.completed_at is not None else None,
        "total_respondents": simulation.total_respondents,
        "progress": {"completed": simulation.completed, "pending": simulation.pending},
        "responses_count": simulation.completed,
        "statistics_ready": statistics_ready,
    }


def register_survey_routes(
    app: Any,
    *,
    get_services: Callable[..., Any],
) -> None:
    from fastapi import Depends, HTTPException, Path, Query
    from fastapi.responses import FileResponse

    @app.get(
        "/api/surveys",
        response_model=SurveysListResponse,
        tags=["survey"],
        summary="List Surveys",
        description="Returns surveys with pagination.",
    )
    def list_surveys(
        page: int = Query(default=1, ge=1, description="1-based page number."),
        page_size: int = Query(default=20, ge=1, le=200, description="Number of surveys per page."),
        services: Any = Depends(get_services),
    ) -> SurveysListResponse:
        surveys = services.surveys.list_surveys()
        total_items = len(surveys)
        total_pages = max(1, math.ceil(total_items / page_size)) if total_items else 1
        start = (page - 1) * page_size
        end = start + page_size

        items = [_survey_response_payload(survey) for survey in surveys[start:end]]
        return SurveysListResponse(
            items=items,
            paging=PagingMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
        )

    @app.post(
        "/api/surveys",
        response_model=SurveyDetailResponse,
        tags=["survey"],
        summary="Create Survey",
        description="Creates and persists a survey definition.",
    )
    def create_survey(
        payload: SurveyCreateRequest,
        services: Any = Depends(get_services),
    ) -> SurveyDetailResponse:
        try:
            survey = services.surveys.create_survey(_model_payload(payload))
            return _survey_response_payload(survey)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid survey payload: {exc}") from exc

    @app.get(
        "/api/surveys/{survey_id}",
        response_model=SurveyDetailResponse,
        tags=["survey"],
        summary="Get Survey",
        description="Fetches a previously created survey definition.",
    )
    def get_survey(
        survey_id: str = Path(description="Survey identifier to fetch.", examples=["coffee-pref-2026-q1"]),
        services: Any = Depends(get_services),
    ) -> SurveyDetailResponse:
        try:
            survey = services.surveys.get_survey(survey_id)
            simulation_items: List[Dict[str, Any]] = []
            for simulation in services.responses.list_simulations(survey_id):
                simulation_items.append(
                    _simulation_payload(
                        simulation,
                        statistics_ready=services.responses.has_statistics_cache(
                            survey_id,
                            simulation.simulation_id,
                        ),
                    )
                )
            return _survey_response_payload(survey, simulations=simulation_items)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/api/surveys/{survey_id}/simulate",
        response_model=SimulateSurveyResponse,
        tags=["survey"],
        summary="Run Survey Simulation",
        description="Runs survey response synthesis for a chosen survey and respondent group.",
    )
    def simulate_survey(
        payload: SimulateSurveyRequest,
        survey_id: str = Path(description="Survey identifier to simulate.", examples=["coffee-pref-2026-q1"]),
        background: bool = Query(
            default=True,
            description="Run simulation in background when true; return immediate processing status.",
        ),
        services: Any = Depends(get_services),
    ) -> SimulateSurveyResponse:
        try:
            if background:
                result = services.responses.run_simulation_background(
                    survey_id=survey_id,
                    group_id=payload.group_id
                )
            else:
                result = services.responses.run_simulation(
                    survey_id=survey_id,
                    group_id=payload.group_id
                )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Simulation failed: {exc}") from exc

        estimated_minutes = max(1, round(result.total_respondents / 60))
        return SimulateSurveyResponse(
            simulation_id=result.simulation_id,
            status=result.status,
            total_respondents=result.total_respondents,
            progress={"completed": result.completed, "pending": result.pending},
            estimated_time_minutes=estimated_minutes,
        )

    @app.get(
        "/api/surveys/{survey_id}/response-details",
        response_model=SimulationResponseDetailsResponse,
        tags=["survey"],
        summary="Get Simulation Response Details",
        description="Returns structured response documents for a survey simulation.",
    )
    def get_simulation_response_details(
        survey_id: str = Path(description="Survey identifier for response details.", examples=["coffee-pref-2026-q1"]),
        simulation_id: Optional[str] = Query(
            default=None,
            description="Specific simulation identifier. Defaults to the latest simulation when omitted.",
        ),
        services: Any = Depends(get_services),
    ) -> SimulationResponseDetailsResponse:
        try:
            payload = services.responses.get_response_details(
                survey_id=survey_id,
                simulation_id=simulation_id,
            )
            return SimulationResponseDetailsResponse(**payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to load response details: {exc}") from exc

    @app.get(
        "/api/surveys/{survey_id}/responses",
        tags=["survey"],
        summary="Download Simulation Responses",
        description="Downloads simulation responses as a CSV or JSON file for a survey.",
        responses={
            200: {
                "description": "Simulation response export file.",
                "content": {
                    "text/csv": {"schema": {"type": "string", "format": "binary"}},
                    "application/json": {"schema": {"type": "string", "format": "binary"}},
                },
            }
        },
    )
    def get_simulation_results(
        survey_id: str = Path(description="Survey identifier for exported responses.", examples=["coffee-pref-2026-q1"]),
        simulation_id: Optional[str] = Query(
            default=None,
            description="Specific simulation identifier. Defaults to the latest simulation if omitted.",
        ),
        format: str = Query(default="csv", description="Export format: `csv` or `json`."),
        services: Any = Depends(get_services),
    ) -> Any:
        simulations = services.responses.list_simulations(survey_id)
        if not simulations:
            raise HTTPException(status_code=404, detail=f"No simulations found for survey '{survey_id}'")

        chosen = simulation_id or simulations[-1].simulation_id
        normalized_format = (format or "csv").strip().lower()
        if normalized_format not in {"csv", "json"}:
            raise HTTPException(status_code=400, detail="format must be either 'csv' or 'json'")

        try:
            path = services.responses.export_responses(
                survey_id=survey_id,
                format=normalized_format,
                simulation_id=chosen,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to export responses: {exc}") from exc

        media_type = "text/csv" if normalized_format == "csv" else "application/json"
        filename = f"{survey_id}-{chosen}-responses.{normalized_format}"
        return FileResponse(
            path=path,
            media_type=media_type,
            filename=filename,
        )

    @app.get(
        "/api/surveys/{survey_id}/statistics",
        response_model=SurveyStatisticsResponse,
        tags=["survey"],
        summary="Compute Simulation Statistics",
        description="Computes question-level response statistics for a survey simulation.",
    )
    def get_simulation_statistics(
        survey_id: str = Path(description="Survey identifier for statistics.", examples=["coffee-pref-2026-q1"]),
        simulation_id: Optional[str] = Query(
            default=None,
            description="Specific simulation identifier. Defaults to latest simulation when omitted.",
        ),
        services: Any = Depends(get_services),
    ) -> SurveyStatisticsResponse:
        try:
            payload = services.responses.compute_response_statistics(
                survey_id=survey_id,
                simulation_id=simulation_id,
            )
            return SurveyStatisticsResponse(**payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to compute statistics: {exc}") from exc
