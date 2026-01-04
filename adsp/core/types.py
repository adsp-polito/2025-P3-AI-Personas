"""Typed request/response contracts for the runtime system."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Optional user-supplied payloads (future: PDF/image/etc)."""

    type: Literal["text", "pdf", "image", "other"] = "other"
    name: Optional[str] = None
    mime_type: Optional[str] = None
    payload: Optional[Any] = None


class ChatRequest(BaseModel):
    """Input contract for a single persona chat turn."""

    persona_id: str
    query: str

    session_id: Optional[str] = None
    persona_display_name: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)

    top_k: int = 5
    use_tools: bool = False


class Citation(BaseModel):
    """Traceability data pointing back to source evidence."""

    doc_id: Optional[str] = None
    pages: List[int] = Field(default_factory=list)
    persona_id: Optional[str] = None
    indicator_id: Optional[str] = None
    indicator_label: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None


class RetrievedContext(BaseModel):
    """RAG output used to ground prompt construction."""

    context: str = ""
    citations: List[Citation] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Tool call record for explainability (future: MCP integration)."""

    tool: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Output contract for a single persona chat turn."""

    persona_id: str
    answer: str

    context: str = ""
    citations: List[Citation] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)


__all__ = [
    "Attachment",
    "ChatRequest",
    "Citation",
    "RetrievedContext",
    "ToolCall",
    "ChatResponse",
]

