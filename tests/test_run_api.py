"""Tests for the API launcher script."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace


def _load_run_api_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_api.py"
    spec = importlib.util.spec_from_file_location("run_api_script", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_api_passes_workers_to_uvicorn(monkeypatch):
    module = _load_run_api_module()
    calls = []

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=lambda *a, **k: calls.append((a, k))))
    monkeypatch.setenv("ADSP_API_RUN_MODE", "uvicorn")
    monkeypatch.setenv("ADSP_API_RELOAD", "false")
    monkeypatch.setenv("ADSP_API_WORKERS", "3")
    monkeypatch.setattr(sys, "argv", ["run_api.py"])

    module.main()

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == ("adsp.app.api_server:app",)
    assert kwargs["workers"] == 3
    assert kwargs["reload"] is False


def test_run_api_forces_single_worker_when_reload_enabled(monkeypatch, capsys):
    module = _load_run_api_module()
    calls = []

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=lambda *a, **k: calls.append((a, k))))
    monkeypatch.setenv("ADSP_API_RUN_MODE", "uvicorn")
    monkeypatch.setenv("ADSP_API_RELOAD", "true")
    monkeypatch.setenv("ADSP_API_WORKERS", "4")
    monkeypatch.setattr(sys, "argv", ["run_api.py"])

    module.main()

    captured = capsys.readouterr()
    assert "workers > 1 is not supported with --reload" in captured.out
    assert calls[0][1]["workers"] == 1


def test_run_api_forces_single_worker_in_direct_mode(monkeypatch, capsys):
    module = _load_run_api_module()
    calls = []

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=lambda *a, **k: calls.append((a, k))))
    monkeypatch.setitem(
        sys.modules,
        "adsp.app.api_server",
        SimpleNamespace(create_app=lambda: "app-instance"),
    )
    monkeypatch.setenv("ADSP_API_RUN_MODE", "direct")
    monkeypatch.setenv("ADSP_API_RELOAD", "false")
    monkeypatch.setenv("ADSP_API_WORKERS", "2")
    monkeypatch.setattr(sys, "argv", ["run_api.py"])

    module.main()

    captured = capsys.readouterr()
    assert "--workers is not supported in --mode direct" in captured.out
    assert calls[0][0] == ("app-instance",)
    assert "workers" not in calls[0][1]
