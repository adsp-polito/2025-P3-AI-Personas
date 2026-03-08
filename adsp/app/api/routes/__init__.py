"""Route registration helpers for the REST API server."""

from .auth import register_auth_routes
from .chat import register_chat_routes
from .groups import register_group_routes
from .ingestion import register_ingestion_routes
from .personas import register_persona_routes
from .reports import register_report_routes
from .surveys import register_survey_routes
from .system import register_system_routes

__all__ = [
    "register_auth_routes",
    "register_chat_routes",
    "register_group_routes",
    "register_ingestion_routes",
    "register_persona_routes",
    "register_report_routes",
    "register_survey_routes",
    "register_system_routes",
]
