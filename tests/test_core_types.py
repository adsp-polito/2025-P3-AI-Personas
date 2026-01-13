"""Core request/response data type coverage."""

import pytest
from pydantic import ValidationError

from adsp.core.types import Attachment
from adsp.core.types import ChatRequest
from adsp.core.types import ChatResponse
from adsp.core.types import Citation
from adsp.core.types import RetrievedContext
from adsp.core.types import ToolCall


def make_request(**overrides) -> ChatRequest:
    payload = {
        'persona_id': 'test_persona',
        'query': 'hello',
        'session_id': None,
        'persona_display_name': None,
        'attachments': [],
        'top_k': 5,
        'use_tools': False,
    }
    payload.update(overrides)
    return ChatRequest(**payload)


def make_citation(**overrides) -> Citation:
    payload = {
        'doc_id': None,
        'pages': [],
        'persona_id': None,
        'indicator_id': None,
        'indicator_label': None,
        'domain': None,
        'category': None,
        'snippet': None,
        'score': None,
    }
    payload.update(overrides)
    return Citation(**payload)


def make_response(**overrides) -> ChatResponse:
    payload = {
        'persona_id': 'p1',
        'answer': 'Hello there',
        'context': '',
        'citations': [],
        'tool_calls': [],
    }
    payload.update(overrides)
    return ChatResponse(**payload)


def make_attachment(**overrides) -> Attachment:
    payload = {
        'type': 'other',
        'name': None,
        'mime_type': None,
        'payload': None,
    }
    payload.update(overrides)
    return Attachment(**payload)


def test_request_requires_persona_id_and_query():
    with pytest.raises(ValidationError):
        ChatRequest(persona_id='p1')

    with pytest.raises(ValidationError):
        ChatRequest(query='hello')


def test_request_defaults_are_set():
    req = make_request()
    assert req.persona_id == 'test_persona'
    assert req.query == 'hello'
    assert req.session_id is None
    assert req.persona_display_name is None
    assert req.top_k == 5
    assert req.use_tools is False
    assert req.attachments == []


def test_request_accepts_optional_fields():
    req = make_request(
        persona_id='p1',
        query='test query',
        session_id='session_123',
        persona_display_name='Test Persona',
        top_k=10,
        use_tools=True,
    )

    assert req.persona_id == 'p1'
    assert req.query == 'test query'
    assert req.session_id == 'session_123'
    assert req.persona_display_name == 'Test Persona'
    assert req.top_k == 10
    assert req.use_tools is True


def test_request_attachments_default_is_list():
    req = make_request()
    assert isinstance(req.attachments, list)
    assert req.attachments == []


def test_request_accepts_attachment_objects():
    att = make_attachment(type='text', name='note.txt', mime_type='text/plain', payload='hi')
    req = make_request(attachments=[att])

    assert len(req.attachments) == 1
    assert req.attachments[0].name == 'note.txt'
    assert req.attachments[0].type == 'text'


def test_request_accepts_attachment_dicts():
    req = make_request(
        attachments=[
            {'type': 'image', 'name': 'photo.png', 'mime_type': 'image/png', 'payload': '...'}
        ]
    )

    assert len(req.attachments) == 1
    assert req.attachments[0].type == 'image'
    assert req.attachments[0].name == 'photo.png'


def test_request_attachments_are_not_shared():
    req_a = make_request()
    req_b = make_request()

    req_a.attachments.append(make_attachment(name='a.txt'))

    assert len(req_a.attachments) == 1
    assert len(req_b.attachments) == 0


def test_citation_defaults():
    citation = Citation()

    assert citation.doc_id is None
    assert citation.pages == []
    assert citation.score is None


def test_citation_with_all_fields():
    citation = make_citation(
        doc_id='doc_123',
        pages=[1, 2, 3],
        persona_id='p1',
        indicator_id='ind_1',
        indicator_label='Test Indicator',
        domain='test_domain',
        category='test_category',
        snippet='This is a test snippet',
        score=0.95,
    )

    assert citation.doc_id == 'doc_123'
    assert citation.pages == [1, 2, 3]
    assert citation.persona_id == 'p1'
    assert citation.indicator_id == 'ind_1'
    assert citation.indicator_label == 'Test Indicator'
    assert citation.domain == 'test_domain'
    assert citation.category == 'test_category'
    assert citation.snippet == 'This is a test snippet'
    assert citation.score == 0.95


def test_citation_pages_are_list():
    citation = make_citation(pages=[1, 4])
    assert isinstance(citation.pages, list)
    assert citation.pages == [1, 4]


def test_retrieved_context_defaults():
    context = RetrievedContext()

    assert context.context == ''
    assert context.citations == []
    assert context.raw == {}


def test_retrieved_context_with_citations():
    citations = [
        make_citation(indicator_id='ind_1', score=0.9),
        make_citation(indicator_id='ind_2', score=0.8),
    ]

    context = RetrievedContext(
        context='Retrieved text here',
        citations=citations,
        raw={'source': 'test'},
    )

    assert len(context.citations) == 2
    assert context.citations[0].indicator_id == 'ind_1'
    assert context.citations[1].indicator_id == 'ind_2'
    assert context.raw['source'] == 'test'


def test_retrieved_context_raw_isolated_per_instance():
    ctx_a = RetrievedContext()
    ctx_b = RetrievedContext()

    ctx_a.raw['key'] = 'value'

    assert 'key' in ctx_a.raw
    assert 'key' not in ctx_b.raw


def test_tool_call_defaults():
    tool_call = ToolCall(tool='search')

    assert tool_call.tool == 'search'
    assert tool_call.payload == {}
    assert tool_call.result is None


def test_tool_call_with_payload_and_result():
    tool_call = ToolCall(tool='search', payload={'q': 'hi'}, result={'ok': True})

    assert tool_call.tool == 'search'
    assert tool_call.payload == {'q': 'hi'}
    assert tool_call.result == {'ok': True}


def test_tool_call_payload_isolated_per_instance():
    tool_a = ToolCall(tool='a')
    tool_b = ToolCall(tool='b')

    tool_a.payload['x'] = 1

    assert tool_a.payload == {'x': 1}
    assert tool_b.payload == {}


def test_response_defaults():
    resp = make_response()

    assert resp.persona_id == 'p1'
    assert resp.answer == 'Hello there'
    assert resp.context == ''
    assert resp.citations == []
    assert resp.tool_calls == []


def test_response_with_citations():
    citations = [make_citation(indicator_id='price', score=0.95)]

    resp = make_response(
        answer='The price is low.',
        context='Price range is low.',
        citations=citations,
    )

    assert len(resp.citations) == 1
    assert resp.context == 'Price range is low.'
    assert resp.citations[0].indicator_id == 'price'


def test_response_with_tool_calls():
    tool_calls = [ToolCall(tool='search', payload={'q': 'price'}, result={'hit': 1})]
    resp = make_response(tool_calls=tool_calls)

    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].tool == 'search'
    assert resp.tool_calls[0].payload['q'] == 'price'
    assert resp.tool_calls[0].result == {'hit': 1}


def test_response_citations_are_isolated():
    resp_a = make_response()
    resp_b = make_response()

    resp_a.citations.append(make_citation(indicator_id='x'))

    assert len(resp_a.citations) == 1
    assert resp_b.citations == []


def test_attachment_defaults():
    att = Attachment()

    assert att.type == 'other'
    assert att.name is None
    assert att.mime_type is None
    assert att.payload is None


def test_attachment_with_fields():
    att = make_attachment(type='image', name='photo.png', mime_type='image/png', payload='...')

    assert att.type == 'image'
    assert att.name == 'photo.png'
    assert att.mime_type == 'image/png'
    assert att.payload == '...'


def test_attachment_literal_types():
    for att_type in ['text', 'pdf', 'image', 'other']:
        att = make_attachment(type=att_type)
        assert att.type == att_type


def test_attachment_invalid_type_raises():
    with pytest.raises(ValidationError):
        Attachment(type='video')
