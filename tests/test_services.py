"""
Tests for app services, communication, storage, and misc utilities.
"""

from dataclasses import dataclass
import logging
from pathlib import Path

import pytest

from adsp.app.auth_service import AuthService
from adsp.app.ingestion_service import IngestionService
from adsp.app.persona_config import PersonaConfigurationService
from adsp.app.qa_service import QAService
from adsp.app.report_service import ReportService
from adsp.communication.cache import CacheClient
from adsp.communication.event_broker import EventBroker
from adsp.communication.rpc import RPCClient
from adsp.core.types import ChatResponse
from adsp.storage.business_db import BusinessDatabase
from adsp.storage.object_store import get, list_keys, put, put_bytes, _STORE
from adsp.storage.vector_db import VectorDatabase
from adsp.utils.exceptions import PersonaError
from adsp.utils.logging import configure_logging


@dataclass
class FakeOrchestrator:
    answer: str = "ok"

    def handle_query(self, persona_id: str, query: str) -> str:
        return f"{persona_id}:{query}:{self.answer}"

    def handle(self, request) -> ChatResponse:
        return ChatResponse(persona_id=request.persona_id, answer=self.answer)


def test_auth_service_register_and_validate():
    auth = AuthService()
    auth.register("alice", "token-123")
    assert auth.is_authorized("alice", "token-123") is True
    assert auth.is_authorized("alice", "wrong") is False


def test_auth_service_missing_user_is_not_authorized():
    auth = AuthService()
    assert auth.is_authorized("missing", "token") is False


def test_persona_config_register_and_list():
    config = PersonaConfigurationService()
    config.register_persona("b", {"label": "beta"})
    config.register_persona("a", {"label": "alpha"})
    assert config.list_personas() == ["a", "b"]


def test_persona_config_get_persona():
    config = PersonaConfigurationService()
    payload = {"label": "alpha", "active": True}
    config.register_persona("a", payload)
    assert config.get_persona("a") == payload


def test_persona_config_get_missing_persona_raises():
    config = PersonaConfigurationService()
    with pytest.raises(KeyError) as exc:
        config.get_persona("missing")
    assert "missing" in str(exc.value)


def test_ingestion_service_ingest_files(tmp_path: Path):
    _STORE.clear()
    file_one = tmp_path / "a.txt"
    file_two = tmp_path / "b.txt"
    file_one.write_text("alpha", encoding="utf-8")
    file_two.write_text("beta", encoding="utf-8")

    service = IngestionService(bucket="docs")
    service.ingest_files([file_one, file_two])

    assert get("docs", "a.txt") == b"alpha"
    assert get("docs", "b.txt") == b"beta"


def test_ingestion_service_ingest_bytes():
    _STORE.clear()
    service = IngestionService(bucket="raw")
    key = service.ingest_bytes("payload.bin", b"data")
    assert key == "payload.bin"
    assert get("raw", "payload.bin") == b"data"


def test_ingestion_service_custom_bucket():
    _STORE.clear()
    service = IngestionService(bucket="default")
    key = service.ingest_bytes("x.bin", b"one", bucket="alt")
    assert key == "x.bin"
    assert get("alt", "x.bin") == b"one"


def test_report_service_generate(tmp_path: Path):
    service = ReportService(output_dir=tmp_path)
    report = service.generate("persona-1", {"score": 8})
    assert report.exists()
    assert report.read_text(encoding="utf-8").startswith("# Insights for persona-1")


def test_qa_service_ask_uses_orchestrator():
    qa = QAService(orchestrator=FakeOrchestrator())
    answer = qa.ask(persona_id="p1", query="hello")
    assert answer == "p1:hello:ok"


def test_qa_service_ask_with_metadata_returns_response():
    qa = QAService(orchestrator=FakeOrchestrator(answer="ready"))
    response = qa.ask_with_metadata(persona_id="p1", query="hello", session_id="s1", top_k=3)
    assert response.persona_id == "p1"
    assert response.answer == "ready"


def test_cache_client_set_and_get():
    cache = CacheClient()
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_cache_client_missing_key_returns_none():
    cache = CacheClient()
    assert cache.get("missing") is None


def test_cache_client_overwrites_value():
    cache = CacheClient()
    cache.set("key", "one")
    cache.set("key", "two")
    assert cache.get("key") == "two"


def test_event_broker_publish_calls_subscribers():
    broker = EventBroker()
    received = []

    def handler(payload: dict) -> None:
        received.append(payload.get("value"))

    broker.subscribe("topic", handler)
    broker.publish("topic", {"value": 1})
    broker.publish("topic", {"value": 2})
    assert received == [1, 2]


def test_event_broker_multiple_subscribers():
    broker = EventBroker()
    calls = {"a": 0, "b": 0}

    def handler_a(payload: dict) -> None:
        calls["a"] += payload.get("inc", 0)

    def handler_b(payload: dict) -> None:
        calls["b"] += payload.get("inc", 0)

    broker.subscribe("topic", handler_a)
    broker.subscribe("topic", handler_b)
    broker.publish("topic", {"inc": 2})
    assert calls == {"a": 2, "b": 2}


def test_event_broker_isolated_topics():
    broker = EventBroker()
    received = []

    def handler(payload: dict) -> None:
        received.append(payload.get("value"))

    broker.subscribe("alpha", handler)
    broker.publish("beta", {"value": 9})
    assert received == []


def test_rpc_client_calls_resolved_handler():
    def resolver(service: str):
        def handler(payload: dict) -> str:
            return f"{service}:{payload.get('value')}"

        return handler

    client = RPCClient(_resolver=resolver)
    assert client.call("svc", {"value": "ok"}) == "svc:ok"


def test_rpc_client_allows_multiple_services():
    def resolver(service: str):
        if service == "a":
            return lambda payload: payload.get("x")
        return lambda payload: payload.get("y")

    client = RPCClient(_resolver=resolver)
    assert client.call("a", {"x": 1}) == 1
    assert client.call("b", {"y": 2}) == 2


def test_object_store_put_and_get(tmp_path: Path):
    _STORE.clear()
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello", encoding="utf-8")
    put("bucket", file_path)
    assert get("bucket", "doc.txt") == b"hello"


def test_object_store_put_bytes_and_list_keys():
    _STORE.clear()
    put_bytes("bucket", "a.bin", b"one")
    put_bytes("bucket", "b.bin", b"two")
    assert list_keys("bucket") == ["a.bin", "b.bin"]


def test_object_store_list_keys_empty_bucket():
    _STORE.clear()
    assert list_keys("missing") == []


def test_object_store_multiple_buckets_are_isolated():
    _STORE.clear()
    put_bytes("a", "file.txt", b"one")
    put_bytes("b", "file.txt", b"two")
    assert get("a", "file.txt") == b"one"
    assert get("b", "file.txt") == b"two"


def test_business_db_upsert_and_fetch():
    db = BusinessDatabase()
    db.upsert("users", "alice", {"role": "admin"})
    assert db.fetch("users", "alice") == {"role": "admin"}


def test_business_db_fetch_missing_returns_empty_dict():
    db = BusinessDatabase()
    assert db.fetch("users", "missing") == {}


def test_business_db_overwrites_existing_entry():
    db = BusinessDatabase()
    db.upsert("users", "alice", {"role": "viewer"})
    db.upsert("users", "alice", {"role": "admin"})
    assert db.fetch("users", "alice") == {"role": "admin"}


def test_vector_db_upsert_and_search_returns_latest():
    db = VectorDatabase()
    db.upsert("p1", "doc1")
    db.upsert("p1", "doc2")
    assert db.search("p1", "query") == "doc2"


def test_vector_db_search_empty_returns_blank():
    db = VectorDatabase()
    assert db.search("missing", "query") == ""


def test_vector_db_isolated_personas():
    db = VectorDatabase()
    db.upsert("p1", "doc1")
    db.upsert("p2", "doc2")
    assert db.search("p1", "query") == "doc1"
    assert db.search("p2", "query") == "doc2"


def test_persona_error_is_exception():
    err = PersonaError("fail")
    assert isinstance(err, Exception)
    assert str(err) == "fail"


def test_configure_logging_sets_level():
    configure_logging(level=logging.WARNING)
    logger = logging.getLogger()
    assert logger.level == logging.WARNING
