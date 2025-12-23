"""Chat interface component for Streamlit frontend."""

import streamlit as st
from adsp.fe.api_client import APIClient
from adsp.fe.state import (
    get_active_session,
    create_new_session,
    add_message_to_session,
)
from adsp.fe.components.sidebar import render_sidebar
from adsp.fe.components.messages import render_message, render_citations


def render_chat_page():
    """Render the main chat interface."""
    
    # Create API client
    client = APIClient(
        base_url=st.session_state.api_url,
        username=st.session_state.username,
        token=st.session_state.api_token,
    )
    
    # Render sidebar
    render_sidebar(client)
    
    # Main chat area
    st.html('<div class="main-header">Lavazza AI Personas Chat</div>')
    
    # Get active session
    active_session = get_active_session()
    
    if not active_session:
        st.info("Please select a persona from the sidebar to start chatting")
        return
    
    # Display session info
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**Chatting with:** {active_session.persona_name}")
    with col2:
        st.markdown(f"**Session:** {active_session.session_id[:8]}...")
    with col3:
        if st.button("Clear Chat"):
            active_session.messages.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Chat messages container
    messages_container = st.container()
    
    with messages_container:
        if not active_session.messages:
            st.info("Start the conversation by typing a message below!")
        else:
            for message in active_session.messages:
                render_message(message)
                
                # Show context and citations if available
                if st.session_state.show_context and message.role == "assistant":
                    if message.context:
                        with st.expander("Retrieved Context"):
                            st.text(message.context)
                    
                    if message.citations:
                        render_citations(message.citations)
    
    # Chat input area
    st.markdown("---")
    
    # Settings
    with st.expander("Chat Settings"):
        col1, col2 = st.columns(2)
        with col1:
            show_context = st.checkbox(
                "Show retrieved context",
                value=st.session_state.show_context,
                help="Display the RAG context and citations used to generate responses",
            )
            if show_context != st.session_state.show_context:
                st.session_state.show_context = show_context
                st.rerun()
        
        with col2:
            top_k = st.slider(
                "Number of context documents (top-k)",
                min_value=1,
                max_value=20,
                value=st.session_state.top_k,
                help="Number of relevant documents to retrieve from RAG",
            )
            if top_k != st.session_state.top_k:
                st.session_state.top_k = top_k
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message:",
            placeholder="Ask me anything about coffee...",
            height=100,
            key="chat_input",
        )
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            submit = st.form_submit_button("Send", width="stretch")
        with col3:
            if st.form_submit_button("New Chat", width="stretch"):
                create_new_session(active_session.persona_id, active_session.persona_name)
                st.rerun()
        
        if submit and user_input.strip():
            handle_chat_submission(client, active_session.session_id, user_input.strip())

def handle_chat_submission(client: APIClient, session_id: str, user_input: str):
    """Handle chat message submission."""
    
    session = st.session_state.chat_sessions.get(session_id)
    if not session:
        st.error("Session not found")
        return
    
    # Add user message
    add_message_to_session(session_id, "user", user_input)
    
    # Send to API
    with st.spinner("Thinking..."):
        response = client.send_chat_message(
            persona_id=session.persona_id,
            query=user_input,
            session_id=session_id,
            top_k=st.session_state.top_k,
        )
    
    if response:
        # Extract response data
        answer = response.get("answer", "I'm sorry, I couldn't generate a response.")
        context = response.get("context", "")
        citations = response.get("citations", [])
        
        # If no context found
        if not context and not citations:
            context = "No relevant documents found in RAG for this query. Answer generated from general knowledge."
        
        # Add assistant message
        add_message_to_session(
            session_id,
            "assistant",
            answer,
            context=context,
            citations=citations,
        )
        
        st.rerun()
    else:
        st.error("Failed to get response from the API. Please try again.")