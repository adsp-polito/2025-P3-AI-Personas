"""Main Streamlit frontend application for AI Personas chat interface."""

import streamlit as st

from adsp.fe.components.auth import render_auth_page
from adsp.fe.components.chat import render_chat_page
from adsp.fe.state import initialize_session_state

def main():
    """Main application entry point."""
    
    # Page configuration
    st.set_page_config(
        page_title="Lavazza AI Personas",
        page_icon=":coffee:",
        layout="wide",
        initial_sidebar_state="auto",
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS for better styling
    st.html("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #041524;
            text-align: center;
            margin-bottom: 1rem;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            max-width: 70%;
            word-wrap: break-word;
        }
        .user-message {
            background-color: #E3F2FD;
            border-left: 4px solid #2196F3;
            margin-left: auto;
            text-align: left;
        }
        .assistant-message {
            background-color: #FFF3E0;
            border-left: 4px solid #FF9800;
            margin-right: auto;
        }
        .stButton button {
            width: 100%;
        }
        </style>
    """)
    
    # Check authentication status
    if not st.session_state.get("authenticated", False):
        render_auth_page()
    else:
        render_chat_page()


if __name__ == "__main__":
    main()