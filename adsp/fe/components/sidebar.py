"""Sidebar component for navigation and persona selection."""

import streamlit as st
from adsp.fe.api_client import APIClient
from adsp.fe.state import create_new_session, get_active_session


def render_sidebar(client: APIClient):
    """Render the application sidebar."""
    
    with st.sidebar:
        # User info
        st.html(f"""
            <div style="font-size: 2rem; font-weight: bold; color: #041524; margin-bottom: 1rem;">
                Welcome, {st.session_state.username}
            </div>
        """)
        
        if st.button("Logout", width="stretch", type="primary"):
            # Clear session
            api_url = st.session_state.api_url  # Keep API URL
            
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.api_token = ""
            st.session_state.personas = []
            st.session_state.selected_persona = None
            st.session_state.chat_sessions.clear()
            st.session_state.active_session_id = None
            st.session_state.show_context = False
            st.session_state.top_k = 5
            
            st.session_state.api_url = api_url  # Restore API URL
            st.rerun()
        
        st.markdown("---")
        
        # Persona selection
        st.markdown("### Select Persona")
        
        # Load personas if not already loaded
        if not st.session_state.personas:
            with st.spinner("Loading personas..."):
                personas = client.list_personas()
                st.session_state.personas = personas
        
        if not st.session_state.personas:
            st.warning("No personas available")
            return
        
        # Display personas as buttons
        for persona in st.session_state.personas:
            persona_id = persona.get("persona_id", "")
            persona_name = persona.get("persona_name", persona_id)
            summary_bio = persona.get("summary_bio", "")
            
            # Skip invalid personas
            if not persona_id or persona_id == "None" or not persona_name or persona_name in ["Classic Local"]:
                continue

            name_parts = persona_name.replace("-", " ").split()
            if len(name_parts) > 2 or len(name_parts) < 2:
                continue
            
            # Check if this is the active persona
            active_session = get_active_session()
            is_active = active_session and active_session.persona_id == persona_id
            
            button_label = f"{'✓' if is_active else '○'} {persona_name}"
            
            with st.container():
                if st.button(button_label, key=f"persona_{persona_id}", width="stretch"):
                    # Show name input dialog
                    st.session_state.show_name_input = True
                    st.session_state.selected_persona_for_name = {
                        "persona_id": persona_id,
                        "persona_name": persona_name
                    }
                    st.rerun()
                
                if summary_bio:
                    with st.expander(f"About {persona_name}", expanded=False):
                        st.caption(summary_bio)
        
        st.markdown("---")
        
        # Chat sessions
        st.markdown("### Chat Sessions")
        
        if not st.session_state.chat_sessions:
            st.caption("No active sessions")
        else:
            for session_id, session in st.session_state.chat_sessions.items():
                is_active = st.session_state.active_session_id == session_id
                
                display_text = session.display_name[:15] + ("..." if len(session.display_name) > 15 else "")
                session_label = f"{'✓' if is_active else '○'} {display_text}"
                msg_count = len(session.messages)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"{session_label} ({msg_count})",
                        key=f"session_{session_id}",
                        width="stretch",
                    ):
                        st.session_state.active_session_id = session_id
                        st.session_state.show_name_input = False
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"delete_{session_id}"):
                        del st.session_state.chat_sessions[session_id]
                        if st.session_state.active_session_id == session_id:
                            st.session_state.active_session_id = None
                        st.rerun()
        
        st.markdown("---")
        
        # API info
        with st.expander("API Info"):
            st.caption(f"**Server:** {st.session_state.api_url}")
            api_status = "🟢 Online" if client.health_check() else "🔴 Offline"
            st.caption(f"**Status:** {api_status}")