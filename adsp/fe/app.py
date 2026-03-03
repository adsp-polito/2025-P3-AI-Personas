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
    
    # Custom dark-theme CSS with higher contrast for readability
    st.html("""
        <style>
        :root {
            --app-bg: #0f1419;
            --panel-bg: #182028;
            --panel-bg-soft: #202a34;
            --panel-border: #31404f;
            --text-primary: #f3f7fb;
            --text-secondary: #c2cfdb;
            --accent: #7cc6ff;
            --accent-strong: #3f99dd;
            --user-bg: #123047;
            --assistant-bg: #24303b;
            --success-bg: #123527;
            --warning-bg: #3a2e12;
            --error-bg: #4a2020;
        }
        .stApp {
            background: linear-gradient(180deg, #0d1217 0%, var(--app-bg) 100%);
            color: var(--text-primary);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #131a21 0%, #10161c 100%);
            border-right: 1px solid var(--panel-border);
        }
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--text-primary);
            text-align: center;
            margin-bottom: 1rem;
            letter-spacing: 0.02em;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.85rem;
            margin-bottom: 1rem;
            max-width: 70%;
            word-wrap: break-word;
            color: var(--text-primary);
            line-height: 1.55;
            border: 1px solid var(--panel-border);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
        }
        .user-message {
            background-color: var(--user-bg);
            border-left: 4px solid var(--accent);
            margin-left: auto;
            text-align: left;
        }
        .assistant-message {
            background-color: var(--assistant-bg);
            border-left: 4px solid #8fb3c9;
            margin-right: auto;
        }
        .chat-message strong {
            color: #ffffff;
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] label,
        [data-testid="stExpander"] label,
        .stCaption,
        .stText,
        .stCodeBlock {
            color: var(--text-primary);
        }
        [data-testid="stAlertContainer"] {
            color: var(--text-primary);
        }
        [data-testid="stInfo"] {
            background: rgba(124, 198, 255, 0.12);
            border: 1px solid rgba(124, 198, 255, 0.28);
        }
        [data-testid="stSuccess"] {
            background: rgba(18, 53, 39, 0.85);
            border: 1px solid rgba(95, 201, 138, 0.28);
        }
        [data-testid="stWarning"] {
            background: rgba(58, 46, 18, 0.9);
            border: 1px solid rgba(255, 204, 102, 0.28);
        }
        [data-testid="stError"] {
            background: rgba(74, 32, 32, 0.88);
            border: 1px solid rgba(255, 135, 135, 0.24);
        }
        [data-testid="stTextInputRootElement"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input {
            background-color: var(--panel-bg);
            color: var(--text-primary);
            border: 1px solid var(--panel-border);
        }
        [data-testid="stTextInputRootElement"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {
            color: var(--text-secondary);
        }
        [data-testid="stExpander"] details,
        [data-testid="stForm"],
        [data-testid="stTabs"],
        [data-testid="stVerticalBlock"] [data-testid="stContainer"] {
            color: var(--text-primary);
        }
        [data-testid="stTab"] {
            color: var(--text-secondary);
        }
        [data-testid="stTab"][aria-selected="true"] {
            color: var(--text-primary);
        }
        .stButton button,
        .stFormSubmitButton button {
            width: 100%;
            background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
            color: #081018;
            border: none;
            font-weight: 700;
        }
        .stButton button:hover,
        .stFormSubmitButton button:hover {
            filter: brightness(1.05);
        }
        .stButton button[kind="secondary"],
        .stFormSubmitButton button[kind="secondary"] {
            background: var(--panel-bg-soft);
            color: var(--text-primary);
            border: 1px solid var(--panel-border);
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
