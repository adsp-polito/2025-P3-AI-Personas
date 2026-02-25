"""Tests for persona hashing helpers."""

from pathlib import Path

from adsp.data_pipeline.persona_data_pipeline.extract_raw.persona_hasher import (
    compute_persona_hash,
    compute_persona_hashes,
    load_existing_persona_bundle,
    merge_persona_maps,
    write_personas_map_bundle,
)


def test_compute_persona_hash_is_stable():
    persona = {
        "persona_id": "p1",
        "persona_name": "Alpha",
        "indicators": [{"id": "i1", "label": "Taste"}],
    }

    first = compute_persona_hash(persona)
    second = compute_persona_hash(persona)

    assert first == second
    assert isinstance(first, str)
    assert first


def test_compute_persona_hash_ignores_runtime_hash_fields():
    base = {
        "persona_id": "p1",
        "persona_name": "Alpha",
        "indicators": [{"id": "i1", "label": "Taste"}],
    }
    with_runtime_fields = {
        **base,
        "persona_hash": "old",
        "reasoned_for_hash": True,
        "reasoned_hash": "old",
    }

    assert compute_persona_hash(base) == compute_persona_hash(with_runtime_fields)


def test_compute_persona_hashes_returns_map():
    personas_map = {
        "p1": {"persona_id": "p1", "persona_name": "Alpha"},
        "p2": {"persona_id": "p2", "persona_name": "Beta"},
    }

    hashes = compute_persona_hashes(personas_map)

    assert set(hashes.keys()) == {"p1", "p2"}
    assert hashes["p1"] != hashes["p2"]


def test_merge_persona_maps_merges_and_deduplicates_indicators():
    existing = {
        "p1": {
            "persona_id": "p1",
            "persona_name": "Alpha",
            "indicators": [
                {"id": "i1", "label": "Taste", "description": "Old"},
            ],
        }
    }
    incoming = {
        "p1": {
            "persona_id": "p1",
            "persona_name": "Alpha",
            "indicators": [
                {"id": "i1", "label": "Taste", "description": "New"},
                {"id": "i2", "label": "Price"},
            ],
        }
    }

    merged = merge_persona_maps(existing, incoming)

    assert set(merged.keys()) == {"p1"}
    indicators = merged["p1"].get("indicators") or []
    assert len(indicators) == 2
    by_id = {item.get("id"): item for item in indicators if isinstance(item, dict)}
    assert by_id["i1"]["description"] == "New"
    assert by_id["i2"]["label"] == "Price"


def test_bundle_write_and_load_roundtrip(tmp_path: Path):
    path = tmp_path / "personas.json"
    personas_map = {
        "p1": {"persona_id": "p1", "persona_name": "Alpha", "indicators": []},
    }
    persona_hashes = compute_persona_hashes(personas_map)

    write_personas_map_bundle(
        path,
        personas_map,
        persona_hashes,
        general_content={},
        pages=[],
    )
    loaded_map, loaded_hashes = load_existing_persona_bundle(path)

    assert loaded_map["p1"]["persona_id"] == "p1"
    assert loaded_hashes == persona_hashes
