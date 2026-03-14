"""Main Streamlit frontend application for AI Personas chat interface."""

import streamlit as st

from adsp.fe.components.auth import render_auth_page
from adsp.fe.components.chat import render_chat_page
from adsp.fe.state import initialize_session_state


def _hex_to_rgba(color: str, alpha: float) -> str:
    cleaned = str(color).strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(char * 2 for char in cleaned)
    if len(cleaned) != 6:
        return f"rgba(128, 128, 128, {alpha})"

    red = int(cleaned[0:2], 16)
    green = int(cleaned[2:4], 16)
    blue = int(cleaned[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def _inject_theme_css() -> None:
    theme_base = str(st.get_option("theme.base") or "dark").strip().lower()
    primary_color = str(st.get_option("theme.primaryColor") or "#4f8bf9")
    secondary_background = str(st.get_option("theme.secondaryBackgroundColor") or "#f3f4f6")
    text_color = str(st.get_option("theme.textColor") or "#111827")

    user_message_background = _hex_to_rgba(primary_color, 0.14 if theme_base == "light" else 0.18)
    message_border = _hex_to_rgba(text_color, 0.16 if theme_base == "light" else 0.24)
    assistant_border = _hex_to_rgba(text_color, 0.18 if theme_base == "light" else 0.30)
    message_shadow = _hex_to_rgba(text_color, 0.06 if theme_base == "light" else 0.16)

    st.html(
        f"""
        <style>
        .main-header {{
            font-size: 2.5rem;
            font-weight: 700;
            color: inherit;
            text-align: center;
            margin-bottom: 1rem;
            letter-spacing: 0.02em;
        }}
        .sidebar-welcome {{
            font-size: 2rem;
            font-weight: 700;
            color: inherit;
            margin-bottom: 1rem;
        }}
        .chat-message {{
            padding: 1rem;
            border-radius: 0.85rem;
            margin-bottom: 1rem;
            max-width: 70%;
            word-wrap: break-word;
            color: inherit;
            line-height: 1.55;
            border: 1px solid {message_border};
            box-shadow: 0 8px 24px {message_shadow};
        }}
        .user-message {{
            background: {user_message_background};
            border-left: 4px solid {primary_color};
            margin-left: auto;
            text-align: left;
        }}
        .assistant-message {{
            background: {secondary_background};
            border-left: 4px solid {assistant_border};
            margin-right: auto;
        }}
        .chat-message strong {{
            color: inherit;
        }}
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] label,
        [data-testid="stExpander"] label,
        .stCaption,
        .stText,
        .stCodeBlock {{
            color: inherit;
        }}
        </style>
        """
    )


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

    _inject_theme_css()
    
    # Check authentication status
    if not st.session_state.get("authenticated", False):
        render_auth_page()
    else:
        render_chat_page()


if __name__ == "__main__":
    main()
