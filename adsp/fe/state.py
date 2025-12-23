"""Session state management for Streamlit application."""

import streamlit as st
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Optional[str] = None
    citations: Optional[List[dict]] = None


@dataclass
class ChatSession:
    """Represents a chat session with a specific persona."""
    session_id: str
    persona_id: str
    persona_name: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


def initialize_session_state():
    """Initialize all session state variables."""
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    if "api_token" not in st.session_state:
        st.session_state.api_token = ""
    
    if "api_url" not in st.session_state:
        st.session_state.api_url = "http://localhost:8000"
    
    if "personas" not in st.session_state:
        st.session_state.personas = []
    
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None
    
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
    
    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = None
    
    if "show_context" not in st.session_state:
        st.session_state.show_context = False
    
    if "top_k" not in st.session_state:
        st.session_state.top_k = 5


def get_active_session() -> Optional[ChatSession]:
    """Get the currently active chat session."""
    session_id = st.session_state.active_session_id
    if session_id:
        return st.session_state.chat_sessions.get(session_id)
    return None


def create_new_session(persona_id: str, persona_name: str) -> str:
    """Create a new chat session and return its ID."""
    from uuid import uuid4
    
    session_id = str(uuid4())
    session = ChatSession(
        session_id=session_id,
        persona_id=persona_id,
        persona_name=persona_name,
    )
    st.session_state.chat_sessions[session_id] = session
    st.session_state.active_session_id = session_id
    return session_id


def add_message_to_session(session_id: str, role: str, content: str, 
                           context: Optional[str] = None, 
                           citations: Optional[List[dict]] = None):
    """Add a message to a chat session."""
    if session_id in st.session_state.chat_sessions:
        message = ChatMessage(
            role=role,
            content=content,
            context=context,
            citations=citations,
        )
        st.session_state.chat_sessions[session_id].messages.append(message)