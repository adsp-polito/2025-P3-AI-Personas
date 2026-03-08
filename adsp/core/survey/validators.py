"""Validation helpers for survey simulation models."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from .models import (
    PersonaConfig,
    RespondentGroup,
    RespondentProfile,
    SimulationResult,
    Survey,
    SurveyResponse,
)


def _validate_model(model_cls: Any, payload: Any) -> Any:
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(payload)
    return model_cls(**payload)


def validate_survey_definition(payload: Mapping[str, Any]) -> Survey:
    return _validate_model(Survey, dict(payload))


def validate_group_composition(composition: Iterable[Mapping[str, Any]]) -> List[PersonaConfig]:
    return [_validate_model(PersonaConfig, dict(item)) for item in composition]


def validate_respondent_profile(payload: Mapping[str, Any]) -> RespondentProfile:
    return _validate_model(RespondentProfile, dict(payload))


def validate_group(payload: Mapping[str, Any]) -> RespondentGroup:
    return _validate_model(RespondentGroup, dict(payload))


def validate_survey_response(payload: Mapping[str, Any]) -> SurveyResponse:
    return _validate_model(SurveyResponse, dict(payload))


def validate_simulation_result(payload: Mapping[str, Any]) -> SimulationResult:
    return _validate_model(SimulationResult, dict(payload))
