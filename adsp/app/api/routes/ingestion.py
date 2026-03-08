"""Ingestion API routes."""

from __future__ import annotations

import base64
from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "notes.txt",
                "content_base64": "SGVsbG8gTGF2YXp6YSBBSSBQZXJzb25hcyE=",
                "bucket": "uploads",
            }
        }
    )

    filename: str = Field(description="Target object key/filename in object storage.")
    content_base64: str = Field(
        description="File content encoded as Base64 string.",
        examples=["SGVsbG8gTGF2YXp6YSBBSSBQZXJzb25hcyE="],
    )
    bucket: Optional[str] = Field(
        default=None,
        description="Optional destination bucket. Defaults to configured ingestion bucket.",
        examples=["uploads"],
    )


class UploadResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"bucket": "uploads", "key": "notes.txt", "size_bytes": 25}})

    bucket: str = Field(description="Destination bucket where payload was stored.")
    key: str = Field(description="Stored object key.")
    size_bytes: int = Field(description="Decoded payload size in bytes.")


def register_ingestion_routes(
    app: Any,
    *,
    get_services: Callable[..., Any],
    authorize: Callable[..., Any],
) -> None:
    from fastapi import Depends, HTTPException

    @app.post(
        "/v1/ingestion/upload",
        response_model=UploadResponse,
        tags=["ingestion"],
        dependencies=[Depends(authorize)],
        summary="Upload File Payload",
        description="Uploads a Base64 payload into object storage through the ingestion service.",
    )
    def upload(payload: UploadRequest, services: Any = Depends(get_services)) -> UploadResponse:
        try:
            raw = base64.b64decode(payload.content_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {exc}") from exc

        bucket = payload.bucket or services.ingestion.bucket
        key = payload.filename
        services.ingestion.ingest_bytes(key, raw, bucket=bucket)
        return UploadResponse(bucket=bucket, key=key, size_bytes=len(raw))
