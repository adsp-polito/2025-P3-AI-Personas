"""
Tests for persona schema models and parse helpers.
"""

import json
from pathlib import Path

import pytest

from adsp.data_pipeline.persona_data_pipeline.parse import (
    load_individual_personas,
    load_personas_bundle,
)
from adsp.data_pipeline.schema import (
    ContentFilters,
    Indicator,
    Influences,
    Metric,
    PersonaProfileModel,
    ReasoningPolicies,
    Salience,
    Source,
    Statement,
    StyleProfile,
    ValueFrame,
    load_persona_profile,
)


def test_source_defaults_and_extra_fields():
    source = Source(extra_field="value")
    assert source.doc_id is None
    assert source.pages == []
    assert source.extra_field == "value"


def test_metric_defaults_and_extra_fields():
    metric = Metric(extra_field="value")
    assert metric.value is None
    assert metric.unit is None
    assert metric.description is None
    assert metric.extra_field == "value"


def test_salience_defaults_and_extra_fields():
    salience = Salience(extra_field=1)
    assert salience.is_salient is None
    assert salience.extra_field == 1


def test_influences_defaults_and_extra_fields():
    influences = Influences(extra_field=True)
    assert influences.tone is None
    assert influences.extra_field is True


def test_statement_defaults_and_extra_fields():
    statement = Statement(extra_field="value")
    assert statement.metrics == []
    assert statement.extra_field == "value"


def test_indicator_defaults_and_extra_fields():
    indicator = Indicator(extra_field="value")
    assert indicator.sources == []
    assert indicator.statements == []
    assert indicator.extra_field == "value"


def test_style_profile_defaults_and_extra_fields():
    style = StyleProfile(extra_field="value")
    assert style.tone_adjectives == []
    assert style.extra_field == "value"


def test_value_frame_defaults_and_extra_fields():
    frame = ValueFrame(extra_field="value")
    assert frame.priority_rank == []
    assert frame.extra_field == "value"


def test_reasoning_policies_defaults_and_extra_fields():
    policies = ReasoningPolicies(extra_field="value")
    assert policies.purchase_advice is None
    assert policies.extra_field == "value"


def test_content_filters_defaults_and_extra_fields():
    filters = ContentFilters(extra_field="value")
    assert filters.avoid_styles == []
    assert filters.extra_field == "value"


def test_persona_profile_defaults():
    profile = PersonaProfileModel()
    assert profile.indicators == []
    assert profile.key_indicators == []
    assert profile.source_pages == []


def test_persona_profile_nested_objects():
    profile = PersonaProfileModel(
        persona_id="p1",
        indicators=[
            Indicator(
                label="Price",
                statements=[
                    Statement(
                        label="Budget",
                        metrics=[Metric(value=10, unit="$")],
                    )
                ],
            )
        ],
    )
    assert profile.indicators[0].label == "Price"
    assert profile.indicators[0].statements[0].metrics[0].unit == "$"


def test_load_persona_profile_reads_file(tmp_path: Path):
    payload = {"persona_id": "p1", "persona_name": "Alpha"}
    path = tmp_path / "persona.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    profile = load_persona_profile(path)
    assert profile.persona_id == "p1"
    assert profile.persona_name == "Alpha"


def test_load_persona_profile_missing_file_raises(tmp_path: Path):
    missing_path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_persona_profile(missing_path)


def test_load_personas_bundle_from_dict(tmp_path: Path):
    payload = {
        "personas": [
            {"persona_id": "p1", "persona_name": "One"},
            {"persona_id": "p2", "persona_name": "Two"},
        ]
    }
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    personas = load_personas_bundle(path)
    assert len(personas) == 2
    assert personas[0].persona_id == "p1"
    assert personas[1].persona_name == "Two"


def test_load_personas_bundle_handles_missing_list(tmp_path: Path):
    payload = {"not_personas": []}
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    personas = load_personas_bundle(path)
    assert personas == []


def test_load_individual_personas_from_directory(tmp_path: Path):
    payload = {"persona_id": "p1", "persona_name": "One"}
    path = tmp_path / "p1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    results = load_individual_personas(tmp_path)
    assert list(results.keys()) == ["p1"]
    assert results["p1"].persona_name == "One"


def test_load_individual_personas_sets_persona_id_from_filename(tmp_path: Path):
    payload = {"persona_name": "Anon"}
    path = tmp_path / "anon.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    results = load_individual_personas(tmp_path)
    assert "anon" in results
    assert results["anon"].persona_id == "anon"
