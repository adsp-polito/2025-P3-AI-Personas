"""Session state management for Streamlit application."""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import streamlit as st


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
    display_name: str
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
        st.session_state.api_url = os.environ.get("ADSP_FE_API_URL", "http://localhost:8000")
    
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
    
    if "waiting_for_response" not in st.session_state:
        st.session_state.waiting_for_response = False
    
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = {}
    
    if "show_name_input" not in st.session_state:
        st.session_state.show_name_input = False
    
    if "selected_persona_for_name" not in st.session_state:
        st.session_state.selected_persona_for_name = None

    if "current_view" not in st.session_state:
        st.session_state.current_view = "chat"

    if "selected_group_id" not in st.session_state:
        st.session_state.selected_group_id = None

    if "selected_survey_id" not in st.session_state:
        st.session_state.selected_survey_id = None

    if "groups_page" not in st.session_state:
        st.session_state.groups_page = 1

    if "surveys_page" not in st.session_state:
        st.session_state.surveys_page = 1

    if "survey_questions_draft" not in st.session_state:
        st.session_state.survey_questions_draft = []

    if "survey_stats_cache" not in st.session_state:
        st.session_state.survey_stats_cache = {}

    if "active_statistics_simulation_id" not in st.session_state:
        st.session_state.active_statistics_simulation_id = None

    if "show_simulation_form" not in st.session_state:
        st.session_state.show_simulation_form = False

    if "show_download_form_simulation_id" not in st.session_state:
        st.session_state.show_download_form_simulation_id = None

    if "prepared_download_payload" not in st.session_state:
        st.session_state.prepared_download_payload = None


def get_sidebar_visible_personas(personas: List[dict]) -> List[dict]:
    """Return personas visible in the sidebar persona list."""
    visible: List[dict] = []
    for persona in personas:
        persona_id = str(persona.get("persona_id", ""))
        persona_name = str(persona.get("persona_name", persona_id))

        if not persona_id or persona_id == "None" or not persona_name or persona_name in ["Classic Local"]:
            continue

        name_parts = persona_name.replace("-", " ").split()
        if len(name_parts) > 2 or len(name_parts) < 2:
            continue

        visible.append(persona)
    return visible


def reset_management_ui_state() -> None:
    """Collapse transient management UI panels."""
    st.session_state.show_simulation_form = False
    st.session_state.show_download_form_simulation_id = None
    st.session_state.prepared_download_payload = None
    st.session_state.active_statistics_simulation_id = None


def get_active_session() -> Optional[ChatSession]:
    """Get the currently active chat session."""
    session_id = st.session_state.active_session_id
    if session_id:
        return st.session_state.chat_sessions.get(session_id)
    return None


def create_new_session(persona_id: str, persona_name: str, display_name: str = None) -> str:
    """Create a new chat session and return its ID."""
    from uuid import uuid4
    
    session_id = str(uuid4())
    session = ChatSession(
        session_id=session_id,
        persona_id=persona_id,
        persona_name=persona_name,
        display_name=display_name or persona_name,
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
