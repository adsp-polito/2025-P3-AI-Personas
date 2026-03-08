"""API startup behavior checks."""

from threading import Event

import pytest


fastapi = pytest.importorskip("fastapi")
unused_fastapi = fastapi


def test_lazy_qa_service_initializes_on_first_use():
    from adsp.app.api_server import LazyQAService

    calls: list[str] = []

    class FakeQA:
        def __init__(self) -> None:
            calls.append("init")
            self.orchestrator = object()

        def ask(self, persona_id: str, query: str) -> str:
            return f"{persona_id}:{query}"

    lazy = LazyQAService(factory=FakeQA)

    assert lazy.status == "idle"
    assert calls == []
    assert lazy.ask("p1", "hello") == "p1:hello"
    assert calls == ["init"]
    assert lazy.status == "ready"


def test_health_does_not_wait_for_qa_warmup(monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    from adsp.app.api_server import create_app

    started = Event()
    release = Event()

    class BlockingQA:
        def __init__(self) -> None:
            started.set()
            release.wait(timeout=2.0)
            self.orchestrator = object()

    monkeypatch.setattr("adsp.app.api_server.QAService", BlockingQA)

    with TestClient(create_app()) as client:
        assert started.wait(timeout=1.0)
        response = client.get("/health")
        payload = response.json()
        release.set()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["qa_status"] == "warming"
