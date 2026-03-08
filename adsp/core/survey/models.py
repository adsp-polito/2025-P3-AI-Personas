"""Data models for survey simulation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

QuestionType = Literal["multiple_choice", "open_ended", "rating"]
AnswerType = Literal["choice", "text", "rating"]


class Question(BaseModel):
    """Single question in a survey."""

    question_id: str
    text: str
    type: QuestionType
    options: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("options", always=True)
    def _validate_options(cls, options: List[str], values: Dict[str, Any]) -> List[str]:
        question_type = values.get("type")
        if question_type == "multiple_choice" and not options:
            raise ValueError("multiple_choice questions require at least one option")
        return options


class Survey(BaseModel):
    """Persisted survey definition."""

    survey_id: str
    title: str
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    questions: List[Question] = Field(default_factory=list)

    @validator("questions")
    def _validate_questions(cls, questions: List[Question]) -> List[Question]:
        if not questions:
            raise ValueError("survey must contain at least one question")
        return questions


class PersonaConfig(BaseModel):
    """Requested number of respondents per persona."""

    persona_id: str
    count: int

    @validator("count")
    def _validate_count(cls, count: int) -> int:
        if count <= 0:
            raise ValueError("count must be > 0")
        return count


class RespondentProfile(BaseModel):
    """Unified simulated respondent profile."""

    respondent_id: str
    persona_id: str
    name: str
    country: Optional[str] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None

    key_indicators: List[Dict[str, Any]] = Field(default_factory=list)
    style_profile: Dict[str, Any] = Field(default_factory=dict)
    value_frame: Dict[str, Any] = Field(default_factory=dict)
    reasoning_policies: Dict[str, Any] = Field(default_factory=dict)
    content_filters: Dict[str, Any] = Field(default_factory=dict)

    generation_method: Literal["random", "llm", "hybrid"] = "random"
    seed: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RespondentGroup(BaseModel):
    """A generated cohort of respondents."""

    group_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    composition: List[PersonaConfig] = Field(default_factory=list)
    respondents: List[RespondentProfile] = Field(default_factory=list)
    generation_method: Literal["random", "llm", "hybrid"] = "random"


class Answer(BaseModel):
    """Single answer to a survey question."""

    question_id: str
    answer_type: AnswerType
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class SurveyResponse(BaseModel):
    """A complete response from one respondent."""

    response_id: str
    survey_id: str
    respondent_id: str
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answers: List[Answer] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Persisted metadata for one simulation run."""

    simulation_id: str
    survey_id: str
    group_id: str
    status: Literal["processing", "completed", "failed"] = "completed"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_respondents: int = 0
    completed: int = 0
    pending: int = 0
    response_ids: List[str] = Field(default_factory=list)
