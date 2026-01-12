"""
Tests for runtime loaders and registries.
"""

import json
from pathlib import Path

import pytest

from adsp.core.input_handler import InputHandler
from adsp.core.persona_registry import PersonaRegistry
from adsp.core.runtime import build_registry, load_personas_from_disk, resolve_persona_paths
from adsp.data_pipeline.schema import PersonaProfileModel


def test_input_handler_normalize_strips_whitespace():
    handler = InputHandler()
    assert handler.normalize("  hello  ") == "hello"


def test_persona_registry_defaults_to_default_persona():
    registry = PersonaRegistry()
    personas = registry.list_personas()
    assert "default" in personas


def test_persona_registry_upsert_and_get():
    registry = PersonaRegistry()
    registry.upsert("p1", {"name": "one"})
    assert registry.get("p1") == {"name": "one"}


def test_persona_registry_upsert_many():
    registry = PersonaRegistry()
    registry.upsert_many([("a", 1), ("b", 2)])
    assert registry.get("a") == 1
    assert registry.get("b") == 2


def test_persona_registry_get_missing_raises():
    registry = PersonaRegistry()
    with pytest.raises(KeyError):
        registry.get("missing")


def test_resolve_persona_paths_defaults(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ADSP_PERSONAS_DIR", raising=False)
    monkeypatch.delenv("ADSP_PERSONA_TRAITS_DIR", raising=False)
    individual, traits = resolve_persona_paths(processed_dir=tmp_path)
    assert individual == tmp_path / "personas" / "individual"
    assert traits == tmp_path / "personas" / "common_traits"


def test_resolve_persona_paths_env_override(tmp_path: Path, monkeypatch):
    custom_individual = tmp_path / "custom_individual"
    custom_traits = tmp_path / "custom_traits"
    monkeypatch.setenv("ADSP_PERSONAS_DIR", str(custom_individual))
    monkeypatch.setenv("ADSP_PERSONA_TRAITS_DIR", str(custom_traits))
    individual, traits = resolve_persona_paths(processed_dir=tmp_path)
    assert individual == custom_individual
    assert traits == custom_traits


def test_load_personas_from_disk_empty_dir(tmp_path: Path):
    personas = load_personas_from_disk(tmp_path)
    assert personas == []


def test_load_personas_from_disk_loads_files(tmp_path: Path):
    payload = {"persona_id": "p1", "persona_name": "One"}
    path = tmp_path / "p1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    personas = load_personas_from_disk(tmp_path)
    assert len(personas) == 1
    assert personas[0].persona_id == "p1"
    assert personas[0].persona_name == "One"


def test_load_personas_from_disk_sets_persona_id_from_filename(tmp_path: Path):
    payload = {"persona_name": "Anon"}
    path = tmp_path / "anon.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    personas = load_personas_from_disk(tmp_path)
    assert personas[0].persona_id == "anon"


def test_load_personas_from_disk_merges_traits(tmp_path: Path):
    individual_dir = tmp_path / "individual"
    traits_dir = tmp_path / "traits"
    individual_dir.mkdir()
    traits_dir.mkdir()

    base_payload = {"persona_id": "p1", "persona_name": "One"}
    traits_payload = {"style_profile": {"formality_level": "high"}}

    (individual_dir / "p1.json").write_text(json.dumps(base_payload), encoding="utf-8")
    (traits_dir / "p1.json").write_text(json.dumps(traits_payload), encoding="utf-8")

    personas = load_personas_from_disk(individual_dir, traits_dir=traits_dir)
    assert personas[0].style_profile.formality_level == "high"


def test_build_registry_from_personas():
    personas = [PersonaProfileModel(persona_id="p1"), PersonaProfileModel(persona_id="p2")]
    registry = build_registry(personas)
    assert registry.get("p1").persona_id == "p1"
    assert registry.get("p2").persona_id == "p2"
