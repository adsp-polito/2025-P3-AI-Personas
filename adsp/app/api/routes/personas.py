"""Persona catalog and prompt API routes."""

from __future__ import annotations

from typing import Any, Callable, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from adsp.core.prompt_builder.system_prompt import (
    persona_to_system_prompt,
    preamble_to_system_prompt,
)
from adsp.data_pipeline.schema import PersonaProfileModel


class PersonaSummary(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "persona_id": "curious-connoisseurs",
                "persona_name": "Curious Connoisseurs",
                "summary_bio": "Enjoys discovering nuanced flavor profiles with informed choices.",
            }
        }
    )

    persona_id: str = Field(description="Stable persona identifier.", examples=["curious-connoisseurs"])
    persona_name: Optional[str] = Field(
        default=None,
        description="Human-readable persona name when available.",
        examples=["Curious Connoisseurs"],
    )
    summary_bio: Optional[str] = Field(
        default=None,
        description="Short persona biography snippet when available.",
    )


class PersonasListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "personas": [
                    {
                        "persona_id": "curious-connoisseurs",
                        "persona_name": "Curious Connoisseurs",
                        "summary_bio": "Enjoys discovering nuanced flavor profiles with informed choices.",
                    }
                ]
            }
        }
    )

    personas: List[PersonaSummary] = Field(
        default_factory=list,
        description="All persona summaries available in the current registry.",
    )


class SystemPromptResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "system_prompt": "You are Curious Connoisseurs. Prioritize flavor depth, craft quality, and exploration."
            }
        }
    )

    system_prompt: str = Field(description="Resolved system prompt used for this persona.")


def register_persona_routes(
    app: Any,
    *,
    get_qa_service: Callable[..., Any],
) -> None:
    from fastapi import Depends, HTTPException, Path

    @app.get(
        "/v1/personas",
        response_model=PersonasListResponse,
        tags=["personas"],
        summary="List Personas",
        description="Returns all personas currently available to the QA orchestrator.",
    )
    def list_personas(qa: Any = Depends(get_qa_service)) -> PersonasListResponse:
        registry = qa.orchestrator.prompt_builder.registry
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

    @app.get(
        "/v1/personas/{persona_id}/profile",
        response_model=PersonaProfileModel,
        tags=["personas"],
        summary="Get Persona Profile",
        description="Returns the full structured profile for a specific persona.",
    )
    def get_persona_profile(
        persona_id: str = Path(description="Persona identifier to fetch.", examples=["curious-connoisseurs"]),
        qa: Any = Depends(get_qa_service),
    ) -> PersonaProfileModel:
        registry = qa.orchestrator.prompt_builder.registry
        persona = registry.get(persona_id)
        if not isinstance(persona, PersonaProfileModel):
            raise HTTPException(status_code=404, detail="Persona profile not available")
        return persona

    @app.get(
        "/v1/personas/{persona_id}/system-prompt",
        response_model=SystemPromptResponse,
        tags=["personas"],
        summary="Get Persona System Prompt",
        description="Builds and returns the active system prompt for a persona.",
    )
    def get_system_prompt(
        persona_id: str = Path(description="Persona identifier to fetch.", examples=["curious-connoisseurs"]),
        qa: Any = Depends(get_qa_service),
    ) -> SystemPromptResponse:
        registry = qa.orchestrator.prompt_builder.registry
        persona = registry.get(persona_id)
        if isinstance(persona, PersonaProfileModel):
            return SystemPromptResponse(system_prompt=persona_to_system_prompt(persona))
        if isinstance(persona, dict):
            return SystemPromptResponse(system_prompt=preamble_to_system_prompt(persona.get("preamble")))
        raise HTTPException(status_code=404, detail="Persona not found")
