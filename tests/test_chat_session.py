"""Chat session data structure checks."""

from adsp.fe.state import ChatMessage
from adsp.fe.state import ChatSession


def make_message(**overrides) -> ChatMessage:
    payload = {
        'role': 'user',
        'content': 'hello',
        'context': None,
        'citations': None,
    }
    payload.update(overrides)
    return ChatMessage(**payload)


def make_session(**overrides) -> ChatSession:
    payload = {
        'session_id': 's1',
        'persona_id': 'p1',
        'persona_name': 'Test Persona',
        'display_name': 'My Persona',
    }
    payload.update(overrides)
    return ChatSession(**payload)


def add_messages(session: ChatSession, messages: list[ChatMessage]) -> None:
    for message in messages:
        session.messages.append(message)


def test_message_defaults():
    msg = make_message()
    assert msg.role == 'user'
    assert msg.content == 'hello'
    assert msg.context is None
    assert msg.citations is None


def test_message_with_context_and_citations():
    citations = [{'doc_id': '123'}, {'doc_id': '456'}]

    msg = make_message(
        role='assistant',
        content='answer',
        context='some context',
        citations=citations,
    )

    assert msg.role == 'assistant'
    assert msg.content == 'answer'
    assert msg.context == 'some context'
    assert isinstance(msg.citations, list)
    assert len(msg.citations) == 2
    assert msg.citations[0]['doc_id'] == '123'
    assert msg.citations[1]['doc_id'] == '456'


def test_message_role_variants():
    for role in ['system', 'assistant', 'user']:
        msg = make_message(role=role)
        assert msg.role == role


def test_message_content_is_string():
    msg = make_message(content='payload')
    assert isinstance(msg.content, str)
    assert msg.content == 'payload'


def test_session_defaults():
    session = make_session()

    assert session.session_id == 's1'
    assert session.persona_id == 'p1'
    assert session.persona_name == 'Test Persona'
    assert session.display_name == 'My Persona'


def test_session_messages_start_empty():
    session = make_session()
    assert isinstance(session.messages, list)
    assert len(session.messages) == 0


def test_session_can_append_message():
    session = make_session()
    session.messages.append(make_message())

    assert len(session.messages) == 1
    assert session.messages[0].content == 'hello'
    assert session.messages[0].role == 'user'


def test_session_preserves_message_order():
    session = make_session()
    messages = [
        make_message(content='first'),
        make_message(content='second'),
        make_message(content='third'),
    ]

    add_messages(session, messages)

    assert [msg.content for msg in session.messages] == ['first', 'second', 'third']


def test_sessions_do_not_share_message_list():
    session_a = make_session(session_id='a')
    session_b = make_session(session_id='b')

    session_a.messages.append(make_message(content='only in a'))

    assert len(session_a.messages) == 1
    assert len(session_b.messages) == 0


def test_session_display_name_defaults():
    session = make_session(persona_name='Test', display_name='Test')
    assert session.display_name == 'Test'
    assert session.persona_name == 'Test'


def test_session_custom_display_name():
    session = make_session(persona_name='Alpha', display_name='Agent Alpha')
    assert session.persona_name == 'Alpha'
    assert session.display_name == 'Agent Alpha'
