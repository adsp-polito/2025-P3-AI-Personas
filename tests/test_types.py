
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


def test_chat_request_with_optional_fields():
    """ChatRequest should accept and store optional fields."""
    req = ChatRequest(
        persona_id="p1",
        query="test query",
        session_id="session_123",
        persona_display_name="Test Persona",
        top_k=10,
        use_tools=True,
    )
    assert req.session_id == "session_123"
    assert req.persona_display_name == "Test Persona"
    assert req.top_k == 10
    assert req.use_tools is True


def test_chat_request_missing_required_fields():
    """ChatRequest should raise ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        ChatRequest(persona_id="p1")

    with pytest.raises(ValidationError):
        ChatRequest(query="hello")


def test_citation_with_all_fields():
    """Citation should accept all optional fields."""
    citation = Citation(
        doc_id="doc_123",
        pages=[1, 2, 3],
        persona_id="p1",
        indicator_id="ind_1",
        indicator_label="Test Indicator",
        domain="test_domain",
        category="test_category",
        snippet="This is a test snippet",
        score=0.95,
    )
    assert citation.doc_id == "doc_123"
    assert citation.pages == [1, 2, 3]
    assert citation.score == 0.95


def test_citation_defaults():
    """Citation should have sensible defaults for all fields."""
    citation = Citation()
    assert citation.doc_id is None
    assert citation.pages == []
    assert citation.score is None


def test_retrieved_context_defaults():
    """RetrievedContext should have empty defaults."""
    context = RetrievedContext()
    assert context.context == ""
    assert context.citations == []
    assert context.raw == {}


def test_retrieved_context_with_citations():
    """RetrievedContext should store citations properly."""
    citations = [
        Citation(indicator_id="ind_1", score=0.9),
        Citation(indicator_id="ind_2", score=0.8),
    ]
    context = RetrievedContext(
        context="Retrieved text here",
        citations=citations,
        raw={"source": "test"},
    )
    assert len(context.citations) == 2
    assert context.citations[0].indicator_id == "ind_1"
    assert context.raw["source"] == "test"

