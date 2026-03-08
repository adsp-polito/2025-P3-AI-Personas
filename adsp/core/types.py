"""Typed request/response contracts for the runtime system."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Optional user-supplied payloads (future: PDF/image/etc)."""

    type: Literal["text", "pdf", "image", "other"] = Field(
        default="other",
        description="Attachment type.",
        examples=["text"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Client-side attachment name.",
        examples=["notes.txt"],
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="Attachment MIME type.",
        examples=["text/plain"],
    )
    payload: Optional[Any] = Field(
        default=None,
        description="Raw attachment payload. Depends on attachment type.",
    )


class ChatRequest(BaseModel):
    """Input contract for a single persona chat turn."""

    persona_id: str = Field(
        description="Persona identifier to answer as.",
        examples=["basic-traditional"],
    )
    query: str = Field(
        description="User question for the selected persona.",
        examples=["What coffee characteristics matter most to you?"],
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for conversation continuity.",
        examples=["session-001"],
    )
    persona_display_name: Optional[str] = Field(
        default=None,
        description="Optional display label for the persona in chat UIs.",
        examples=["Basic Traditional"],
    )
    attachments: List[Attachment] = Field(
        default_factory=list,
        description="Optional file/content attachments provided with the question.",
    )

    top_k: int = Field(
        default=5,
        description="Maximum number of retrieved context chunks used for grounding.",
        examples=[5],
    )
    use_tools: bool = Field(
        default=False,
        description="Whether to allow tool invocation during answer generation.",
    )


class Citation(BaseModel):
    """Traceability data pointing back to source evidence."""

    doc_id: Optional[str] = Field(default=None, description="Source document identifier.")
    pages: List[int] = Field(default_factory=list, description="Source page numbers used in grounding.")
    persona_id: Optional[str] = Field(default=None, description="Persona linked to this citation.")
    indicator_id: Optional[str] = Field(default=None, description="Indicator identifier referenced by the answer.")
    indicator_label: Optional[str] = Field(default=None, description="Human-readable indicator label.")
    domain: Optional[str] = Field(default=None, description="Business domain for the cited indicator.")
    category: Optional[str] = Field(default=None, description="Category grouping for the citation.")
    snippet: Optional[str] = Field(default=None, description="Short cited source snippet.")
    score: Optional[float] = Field(default=None, description="Similarity/relevance score when available.")


class RetrievedContext(BaseModel):
    """RAG output used to ground prompt construction."""

    context: str = Field(default="", description="Assembled textual context from retrieval.")
    citations: List[Citation] = Field(default_factory=list, description="Citation list for retrieved context.")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Backend-specific retrieval payload.")


class ToolCall(BaseModel):
    """Tool call record for explainability (future: MCP integration)."""

    tool: str = Field(description="Tool name invoked by the orchestrator.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool.")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool output payload.")


class ChatResponse(BaseModel):
    """Output contract for a single persona chat turn."""

    persona_id: str = Field(description="Persona identifier that produced the answer.")
    answer: str = Field(description="Natural-language answer text returned to the user.")

    context: str = Field(default="", description="Retrieved context used to generate the answer.")
    citations: List[Citation] = Field(default_factory=list, description="Traceability citations for the answer.")
    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="Tool call records captured during generation.",
    )


__all__ = [
    "Attachment",
    "ChatRequest",
    "Citation",
    "RetrievedContext",
    "ToolCall",
    "ChatResponse",
]
