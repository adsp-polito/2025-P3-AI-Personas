from adsp.app import AuthService, QAService
from adsp.fe import ChatFrontend


def test_chat_frontend_unauthorized():
    auth = AuthService()
    qa = QAService()
    fe = ChatFrontend(qa_service=qa, auth_service=auth)
    assert fe.send_message("alice", "bad-token", "default", "hello") == "Unauthorized"


def test_end_to_end_default_persona_smoke():
    qa = QAService()
    answer = qa.ask(persona_id="default", query="hello")
    assert isinstance(answer, str)
    assert answer
