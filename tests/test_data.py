"""Smoke checks for frontend auth and QA flow."""

from adsp.app import AuthService
from adsp.app import QAService
from adsp.fe import ChatFrontend


DEFAULT_PERSONA = 'default'


def build_services() -> tuple[AuthService, QAService]:
    auth = AuthService()
    qa = QAService()
    return auth, qa


def build_frontend(auth: AuthService | None = None, qa: QAService | None = None) -> ChatFrontend:
    if auth is None or qa is None:
        auth, qa = build_services()
    return ChatFrontend(qa_service=qa, auth_service=auth)


def register(auth: AuthService, user: str, token: str) -> None:
    auth.register(user, token)


def test_frontend_rejects_unknown_user():
    frontend = build_frontend()
    response = frontend.send_message('alice', 'bad-token', DEFAULT_PERSONA, 'hello')
    assert response == 'Unauthorized'


def test_frontend_rejects_wrong_token():
    auth, qa = build_services()
    register(auth, 'alice', 'token-123')
    frontend = build_frontend(auth=auth, qa=qa)

    response = frontend.send_message('alice', 'wrong', DEFAULT_PERSONA, 'hello')
    assert response == 'Unauthorized'


def test_frontend_rejects_wrong_user():
    auth, qa = build_services()
    register(auth, 'alice', 'token-123')
    frontend = build_frontend(auth=auth, qa=qa)

    response = frontend.send_message('bob', 'token-123', DEFAULT_PERSONA, 'hello')
    assert response == 'Unauthorized'


def test_frontend_accepts_valid_credentials():
    auth, qa = build_services()
    register(auth, 'alice', 'token-123')
    frontend = build_frontend(auth=auth, qa=qa)

    response = frontend.send_message('alice', 'token-123', DEFAULT_PERSONA, 'hello')

    assert isinstance(response, str)
    assert response
    assert response != 'Unauthorized'


def test_qa_service_returns_string():
    _, qa = build_services()
    answer = qa.ask(persona_id=DEFAULT_PERSONA, query='hello')

    assert isinstance(answer, str)
    assert answer


def test_qa_service_multiple_calls_are_independent():
    _, qa = build_services()
    answer_one = qa.ask(persona_id=DEFAULT_PERSONA, query='hello')
    answer_two = qa.ask(persona_id=DEFAULT_PERSONA, query='hello')

    assert isinstance(answer_one, str)
    assert isinstance(answer_two, str)
    assert answer_one
    assert answer_two


def test_qa_service_handles_different_queries():
    _, qa = build_services()
    answer_one = qa.ask(persona_id=DEFAULT_PERSONA, query='hello')
    answer_two = qa.ask(persona_id=DEFAULT_PERSONA, query='what is this')

    assert isinstance(answer_one, str)
    assert isinstance(answer_two, str)
    assert answer_one
    assert answer_two
