
import pytest
from pydantic import ValidationError

from adsp.core.types import (
    Attachment,
    ChatRequest,
    ChatResponse,
    Citation,
    RetrievedContext,
    ToolCall,
)


def test_chat_request_minimal():
    """ChatRequest should accept minimal required fields."""
    req = ChatRequest(persona_id="test_persona", query="hello")
    assert req.persona_id == "test_persona"
    assert req.query == "hello"
    assert req.session_id is None
    assert req.top_k == 5
    assert req.use_tools is False
    assert req.attachments == []



