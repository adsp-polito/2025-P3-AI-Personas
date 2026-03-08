"""Chat API routes."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from adsp.core.types import ChatRequest, ChatResponse


class ChatResponseEnvelope(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": {
                    "persona_id": "curious-connoisseurs",
                    "answer": "I look for consistent taste, trusted quality, and fair price.",
                    "context": "",
                    "citations": [],
                    "tool_calls": [],
                }
            }
        }
    )

    response: ChatResponse = Field(description="Persona chat response payload.")


def register_chat_routes(
    app: Any,
    *,
    get_qa_service: Callable[..., Any],
    authorize: Callable[..., Any],
) -> None:
    from fastapi import Depends

    @app.post(
        "/v1/chat",
        response_model=ChatResponseEnvelope,
        tags=["chat"],
        dependencies=[Depends(authorize)],
        summary="Persona Chat",
        description="Runs one persona-grounded chat turn and returns the generated answer.",
    )
    def chat(payload: ChatRequest, qa: Any = Depends(get_qa_service)) -> ChatResponseEnvelope:
        response = qa.orchestrator.handle(payload)
        return ChatResponseEnvelope(response=response)
