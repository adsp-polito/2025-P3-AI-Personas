"""Respondent group API routes."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _available_country_ids_from_profiles() -> List[str]:
    from adsp.core.survey.group_generator import _COUNTRY_PROFILES

    return sorted(_COUNTRY_PROFILES.keys())


def _group_create_description() -> str:
    countries = ", ".join(f"`{country}`" for country in _available_country_ids_from_profiles())
    return (
        "Generates a synthetic respondent group from persona composition input.\n\n"
        f"Available countries for the `countries` field: {countries}.\n"
        "For the latest supported list, use `GET /api/groups/countries`."
    )


class PagingMeta(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20,
                "total_items": 12,
                "total_pages": 1,
            }
        }
    )

    page: int = Field(description="Current page number (1-based).")
    page_size: int = Field(description="Maximum number of items per page.")
    total_items: int = Field(description="Total number of available items.")
    total_pages: int = Field(description="Total number of pages at the selected page size.")


class GroupCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_name": "Q2 Italy test panel",
                "composition": [
                    {"persona_id": "curious-connoisseurs", "count": 25},
                    {"persona_id": "conscious-explorers", "count": 15},
                ],
                "mode": "random",
                "sampling_ratio": 0.7,
                "include_names": True,
                "countries": ["italy", "france"],
                "seed": 42,
            }
        }
    )

    group_name: Optional[str] = Field(
        default=None,
        description="Optional human-readable label for the respondent group.",
    )
    composition: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Group composition list with `persona_id` and `count` per segment.",
    )
    mode: str = Field(default="random", description="Profile generation mode: `random` or `llm`.")
    sampling_ratio: float = Field(
        default=0.7,
        description="Sampling ratio used for trait sub-selection when generating respondents.",
    )
    include_names: bool = Field(default=True, description="Whether to synthesize person-like names for respondents.")
    countries: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional allowed countries for generated respondents. "
            "Use `GET /api/groups/countries` to list supported values."
        ),
    )
    seed: Optional[int] = Field(default=None, description="Optional random seed for deterministic generation.")


class GroupCreateResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_id": "group-ab12cd34",
                "group_name": "Q2 Italy test panel",
                "created_at": "2026-03-08T15:40:03.123000+00:00",
                "total_respondents": 40,
                "composition": [
                    {"persona_id": "curious-connoisseurs", "count": 7},
                    {"persona_id": "conscious-explorers", "count": 5},
                ],
                "generation_method": "random",
                "sample_profiles": [
                    {
                        "respondent_id": "group-ab12cd34-resp-00001",
                        "persona_id": "curious-connoisseurs",
                        "name": "Luca Rossi",
                        "style_profile": {"tone_adjectives": ["clear", "pragmatic"]},
                        "value_frame": {"priority_rank": ["quality", "price"]},
                        "generation_method": "random",
                    }
                ],
            }
        }
    )

    group_id: str = Field(description="Generated respondent group identifier.")
    group_name: Optional[str] = Field(default=None, description="Optional human-readable label for the group.")
    created_at: str = Field(description="Group creation timestamp in ISO-8601 format.")
    total_respondents: int = Field(description="Total number of generated respondents.")
    composition: List[Dict[str, Any]] = Field(default_factory=list, description="Normalized requested composition.")
    generation_method: str = Field(description="Generation method used to build the group.")
    sample_profiles: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Short preview of generated respondent profiles.",
    )


class GroupFetchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_id": "group-ab12cd34",
                "group_name": "Q2 Italy test panel",
                "created_at": "2026-03-08T15:40:03.123000+00:00",
                "total_respondents": 40,
                "composition": [{"persona_id": "curious-connoisseurs", "count": 25}],
                "generation_method": "random",
                "respondents": [],
                "sample_profiles": [
                    {
                        "respondent_id": "group-ab12cd34-resp-00001",
                        "persona_id": "curious-connoisseurs",
                        "name": "Luca Rossi",
                        "style_profile": {"tone_adjectives": ["clear", "pragmatic"]},
                        "value_frame": {"priority_rank": ["quality", "price"]},
                        "generation_method": "random",
                    }
                ],
            }
        }
    )

    group_id: str = Field(description="Respondent group identifier.")
    group_name: Optional[str] = Field(default=None, description="Optional human-readable label for the group.")
    created_at: str = Field(description="Group creation timestamp.")
    total_respondents: int = Field(description="Total respondents in this group.")
    composition: List[Dict[str, Any]] = Field(default_factory=list, description="Group composition by persona segment.")
    generation_method: str = Field(description="Generation method used for the group.")
    respondents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Full respondent payloads (returned only if `include_full_profiles=true`).",
    )
    sample_profiles: List[Dict[str, Any]] = Field(default_factory=list, description="Always-returned sample profiles.")


class GroupsListItemResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_id": "group-ab12cd34",
                "group_name": "Q2 Italy test panel",
                "created_at": "2026-03-08T15:40:03.123000+00:00",
                "total_respondents": 40,
                "composition": [{"persona_id": "curious-connoisseurs", "count": 25}],
                "generation_method": "random",
                "sample_profiles": [
                    {
                        "respondent_id": "group-ab12cd34-resp-00001",
                        "persona_id": "curious-connoisseurs",
                        "name": "Luca Rossi",
                        "style_profile": {"tone_adjectives": ["clear", "pragmatic"]},
                        "value_frame": {"priority_rank": ["quality", "price"]},
                        "generation_method": "random",
                    }
                ],
            }
        }
    )

    group_id: str = Field(description="Respondent group identifier.")
    group_name: Optional[str] = Field(default=None, description="Optional human-readable label for the group.")
    created_at: str = Field(description="Group creation timestamp.")
    total_respondents: int = Field(description="Total respondents in this group.")
    composition: List[Dict[str, Any]] = Field(default_factory=list, description="Group composition by persona segment.")
    generation_method: str = Field(description="Generation method used for the group.")
    sample_profiles: List[Dict[str, Any]] = Field(default_factory=list, description="Preview respondent profiles.")


class GroupsListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "group_id": "group-ab12cd34",
                        "created_at": "2026-03-08T15:40:03.123000+00:00",
                        "total_respondents": 40,
                        "composition": [{"persona_id": "curious-connoisseurs", "count": 25}],
                        "generation_method": "random",
                        "sample_profiles": [],
                    }
                ],
                "paging": {"page": 1, "page_size": 20, "total_items": 12, "total_pages": 1},
            }
        }
    )

    items: List[GroupsListItemResponse] = Field(default_factory=list, description="Paged group list.")
    paging: PagingMeta = Field(description="Paging metadata for the group list.")


def _to_iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _sample_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "respondent_id": profile.get("respondent_id"),
        "persona_id": profile.get("persona_id"),
        "name": profile.get("name"),
        "country": profile.get("country"),
        "gender": profile.get("gender"),
        "ethnicity": profile.get("ethnicity"),
        "style_profile": {
            "tone_adjectives": (profile.get("style_profile") or {}).get("tone_adjectives", [])
        },
        "value_frame": {
            "priority_rank": (profile.get("value_frame") or {}).get("priority_rank", [])
        },
        "generation_method": profile.get("generation_method"),
    }


class GroupCountryItemResponse(BaseModel):
    country_id: str = Field(description="Canonical country id to use in `POST /api/groups`.")
    display_name: str = Field(description="Human-readable country name.")
    description: str = Field(description="Short description of this country profile option.")


class GroupCountriesResponse(BaseModel):
    countries: List[GroupCountryItemResponse] = Field(
        default_factory=list,
        description="List of supported countries for respondent generation.",
    )


def register_group_routes(
    app: Any,
    *,
    get_services: Callable[..., Any],
) -> None:
    from fastapi import Depends, HTTPException, Path, Query

    @app.post(
        "/api/groups",
        response_model=GroupCreateResponse,
        tags=["survey"],
        summary="Create Respondent Group",
        description=_group_create_description(),
    )
    def create_group(
        payload: GroupCreateRequest,
        services: Any = Depends(get_services),
    ) -> GroupCreateResponse:
        try:
            group = services.groups.create_group(
                payload.composition,
                mode=payload.mode,
                group_name=payload.group_name,
                sampling_ratio=payload.sampling_ratio,
                include_names=payload.include_names,
                countries=payload.countries,
                seed=payload.seed,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid group payload: {exc}") from exc

        respondents = [
            profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile.dict()
            for profile in group.respondents
        ]
        return GroupCreateResponse(
            group_id=group.group_id,
            group_name=group.group_name,
            created_at=_to_iso(group.created_at),
            total_respondents=len(group.respondents),
            composition=[
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item.dict()
                for item in group.composition
            ],
            generation_method=group.generation_method,
            sample_profiles=[_sample_profile(profile) for profile in respondents[:3]],
        )

    @app.get(
        "/api/groups/countries",
        response_model=GroupCountriesResponse,
        tags=["survey"],
        summary="List Available Countries",
        description=(
            "Returns all country values accepted by `POST /api/groups` via the `countries` field. "
            "Provide one or more ids from this list to constrain generated respondent demographics."
        ),
    )
    def list_available_countries(
        services: Any = Depends(get_services),
    ) -> GroupCountriesResponse:
        return GroupCountriesResponse(countries=[GroupCountryItemResponse(**item) for item in services.groups.list_available_countries()])

    @app.get(
        "/api/groups",
        response_model=GroupsListResponse,
        tags=["survey"],
        summary="List Respondent Groups",
        description="Returns respondent groups with pagination.",
    )
    def list_groups(
        page: int = Query(default=1, ge=1, description="1-based page number."),
        page_size: int = Query(default=20, ge=1, le=200, description="Number of groups per page."),
        services: Any = Depends(get_services),
    ) -> GroupsListResponse:
        groups = services.groups.list_groups()
        total_items = len(groups)
        total_pages = max(1, math.ceil(total_items / page_size)) if total_items else 1
        start = (page - 1) * page_size
        end = start + page_size

        items: List[GroupsListItemResponse] = []
        for group in groups[start:end]:
            respondents = [
                profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile.dict()
                for profile in group.respondents
            ]
            items.append(
                GroupsListItemResponse(
                    group_id=group.group_id,
                    group_name=group.group_name,
                    created_at=_to_iso(group.created_at),
                    total_respondents=len(group.respondents),
                    composition=[
                        item.model_dump(mode="json") if hasattr(item, "model_dump") else item.dict()
                        for item in group.composition
                    ],
                    generation_method=group.generation_method,
                    sample_profiles=[_sample_profile(profile) for profile in respondents[:3]],
                )
            )

        return GroupsListResponse(
            items=items,
            paging=PagingMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
        )

    @app.get(
        "/api/groups/{group_id}",
        response_model=GroupFetchResponse,
        tags=["survey"],
        summary="Get Respondent Group",
        description="Returns group metadata and optionally all full respondent profiles.",
    )
    def get_group(
        group_id: str = Path(description="Group identifier to fetch.", examples=["group-ab12cd34"]),
        include_full_profiles: bool = Query(
            default=False,
            description="Set true to include all generated respondent profiles in the response.",
        ),
        services: Any = Depends(get_services),
    ) -> GroupFetchResponse:
        try:
            group = services.groups.get_group(group_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        respondents = [
            profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile.dict()
            for profile in group.respondents
        ]
        return GroupFetchResponse(
            group_id=group.group_id,
            group_name=group.group_name,
            created_at=_to_iso(group.created_at),
            total_respondents=len(group.respondents),
            composition=[
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item.dict()
                for item in group.composition
            ],
            generation_method=group.generation_method,
            respondents=respondents if include_full_profiles else [],
            sample_profiles=[_sample_profile(profile) for profile in respondents[:3]],
        )
