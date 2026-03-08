"""Authentication API routes."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"user": "demo-user", "token": "demo-token-123"}})

    user: str = Field(description="Unique user identifier used for API calls.", examples=["demo-user"])
    token: str = Field(description="Token to register for the user.", examples=["demo-token-123"])


class AuthValidateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"user": "demo-user", "token": "demo-token-123"}})

    user: str = Field(description="User identifier to validate.", examples=["demo-user"])
    token: str = Field(description="Token to validate for the user.", examples=["demo-token-123"])


class AuthRegisterResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})

    status: str = Field(description="Registration status.", examples=["ok"])


class AuthValidateResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"authorized": True}})

    authorized: bool = Field(description="Whether the supplied user/token pair is authorized.")


def register_auth_routes(
    app: Any,
    *,
    get_services: Callable[..., Any],
) -> None:
    from fastapi import Depends

    @app.post(
        "/v1/auth/register",
        response_model=AuthRegisterResponse,
        tags=["auth"],
        summary="Register API Token",
        description="Registers or updates the token associated with a user.",
    )
    def register_auth(payload: AuthRegisterRequest, services: Any = Depends(get_services)) -> AuthRegisterResponse:
        services.auth.register(payload.user, payload.token)
        return AuthRegisterResponse(status="ok")

    @app.post(
        "/v1/auth/validate",
        response_model=AuthValidateResponse,
        tags=["auth"],
        summary="Validate API Token",
        description="Checks whether a user/token pair is currently authorized.",
    )
    def validate_auth(
        payload: AuthValidateRequest,
        services: Any = Depends(get_services),
    ) -> AuthValidateResponse:
        return AuthValidateResponse(authorized=services.auth.is_authorized(payload.user, payload.token))
