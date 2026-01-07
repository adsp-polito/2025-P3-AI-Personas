"""
Tests for chat session data structures.

These verify that chat messages and sessions are created correctly.
"""

from adsp.fe.state import ChatMessage, ChatSession


def test_chat_message_creation():
    msg = ChatMessage(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.context is None
    assert msg.citations is None


def test_chat_message_with_citations():
    citations = [{"doc_id": "123"}]
    msg = ChatMessage(
        role="assistant",
        content="answer",
        context="some context",
        citations=citations
    )
    assert msg.role == "assistant"
    assert msg.context == "some context"
    assert len(msg.citations) == 1


def test_chat_session_creation():
    session = ChatSession(
        session_id="s1",
        persona_id="p1",
        persona_name="Test Persona",
        display_name="My Persona"
    )
    assert session.session_id == "s1"
    assert session.persona_id == "p1"
    assert session.display_name == "My Persona"
    assert len(session.messages) == 0


def test_chat_session_default_display_name():
    session = ChatSession(
        session_id="s1",
        persona_id="p1",
        persona_name="Test",
        display_name="Test"
    )
    assert session.display_name == "Test"
