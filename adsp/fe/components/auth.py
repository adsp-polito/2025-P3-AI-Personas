"""Authentication component for Streamlit frontend."""

import streamlit as st
from adsp.fe.api_client import APIClient


def render_auth_page():
    """Render the authentication page."""
    
    st.html('<div class="main-header">Lavazza AI Personas</div>')
    
    st.markdown("---")
    
    # Create columns for centering the form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Authentication")
        
        # API Configuration
        with st.expander("API Configuration", expanded=False):
            api_url = st.text_input(
                "API Server URL",
                value=st.session_state.api_url,
                help="URL of the backend API server",
            )
            if api_url != st.session_state.api_url:
                st.session_state.api_url = api_url
        
        # Check API health
        client = APIClient(base_url=st.session_state.api_url)
        api_status = client.health_check()
        
        if api_status:
            st.success("API server is online")
        else:
            st.error("Cannot connect to API server. Please check the URL and ensure the server is running.")
            st.info("Start the server")
            return
        
        # Authentication tabs
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            render_login_form(client)
        
        with tab2:
            render_register_form(client)

def render_login_form(client: APIClient):
    """Render the login form."""
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        token = st.text_input("Access Token", type="password", key="login_token")
        
        submit = st.form_submit_button("Login", width="stretch")
        
        if submit:
            if not username or not token:
                st.error("Please provide both username and token")
                return
            
            with st.spinner("Validating credentials..."):
                if client.validate_auth(username, token):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.api_token = token
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again or register.")

def render_register_form(client: APIClient):
    """Render the registration form."""
    
    with st.form("register_form"):
        username = st.text_input("Username", key="register_username")
        token = st.text_input("Access Token", type="password", key="register_token")
        token_confirm = st.text_input("Confirm Token", type="password", key="register_token_confirm")
        
        submit = st.form_submit_button("Register", width="stretch")
        
        if submit:
            if not username or not token or not token_confirm:
                st.error("Please fill in all fields")
                return
            
            if token != token_confirm:
                st.error("Tokens do not match")
                return
            
            with st.spinner("Registering user..."):
                if client.register_user(username, token):
                    st.success("Registration successful! You can now login.")
                else:
                    st.error("Registration failed. Please try again.")