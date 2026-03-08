"""Local path setup and deterministic env for survey tests."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _force_stub_llm(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ADSP_LLM_BACKEND", "stub")
