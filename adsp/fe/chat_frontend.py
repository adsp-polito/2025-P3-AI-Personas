"""Stub FE layer representing the user-facing chat application."""

from __future__ import annotations

from dataclasses import dataclass

from adsp.app import QAService, AuthService


@dataclass
class ChatFrontend:
    """Very small abstraction that wires auth and the QA service."""

    qa_service: QAService
    auth_service: AuthService

    def send_message(self, user: str, token: str, persona_id: str, message: str) -> str:
        if not self.auth_service.is_authorized(user, token):
            return "Unauthorized"
        return self.qa_service.ask(persona_id=persona_id, query=message)
