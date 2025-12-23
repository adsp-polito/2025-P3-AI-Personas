"""Message rendering components."""

import streamlit as st
from adsp.fe.state import ChatMessage
from typing import List, Dict, Any


def render_message(message: ChatMessage):
    """Render a single chat message."""
    
    if message.role == "user":
        render_user_message(message)
    else:
        render_assistant_message(message)

def render_user_message(message: ChatMessage):
    """Render a user message."""
    
    with st.container():
        st.markdown(
            f"""
            <div class="chat-message user-message">
                <strong>You:</strong><br>
                {message.content}
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_assistant_message(message: ChatMessage):
    """Render an assistant message."""
    
    with st.container():
        st.markdown(
            f"""
            <div class="chat-message assistant-message">
                <strong>Assistant:</strong><br>
                {message.content}
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_citations(citations: List[Dict[str, Any]]):
    """Render citations from the RAG system."""
    
    if not citations:
        return
    
    with st.expander(f"Citations ({len(citations)})"):
        for idx, citation in enumerate(citations, 1):
            st.markdown(f"**Citation {idx}:**")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if citation.get("persona_id"):
                    st.caption(f"**Persona:** {citation['persona_id']}")
                if citation.get("domain"):
                    st.caption(f"**Domain:** {citation['domain']}")
                if citation.get("category"):
                    st.caption(f"**Category:** {citation['category']}")
                if citation.get("pages"):
                    pages_str = ", ".join(str(p) for p in citation['pages'])
                    st.caption(f"**Pages:** {pages_str}")
            
            with col2:
                if citation.get("indicator_label"):
                    st.caption(f"**Indicator:** {citation['indicator_label']}")
                if citation.get("snippet"):
                    st.caption(f"**Snippet:** {citation['snippet']}")
            
            st.markdown("---")