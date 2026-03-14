"""Group generator unit tests."""

import json
from pathlib import Path

import pytest

from adsp.core.survey import GroupGenerator


@pytest.fixture
def traits_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "traits"
    directory.mkdir(parents=True, exist_ok=True)

    payload = {
        "persona_id": "test-persona",
        "persona_name": "Test Persona",
        "summary_bio": "Synthetic profile used in tests",
        "key_indicators": [
            {
                "indicator_id": "demographics",
                "indicator_category": "Demographics",
                "statement_label": "Age Group",
                "statement_description": "35-44",
                "metrics": [{"value": 42, "unit": "%"}],
                "salience": {"is_salient": True, "magnitude": "strong"},
            },
            {
                "indicator_id": "behaviour",
                "indicator_category": "Behaviors",
                "statement_label": "Coffee Frequency",
                "statement_description": "Daily",
                "metrics": [],
                "salience": {"is_salient": True, "magnitude": "strong"},
            },
        ],
        "style_profile": {
            "tone_adjectives": ["knowledgeable", "friendly", "curious", "pragmatic"],
            "formality_level": "medium",
            "directness": "balanced",
            "emotional_flavour": "enthusiastic",
            "criticality_level": "medium",
            "verbosity_preference": "balanced",
        },
        "value_frame": {
            "priority_rank": ["quality", "sustainability", "price", "innovation"],
            "sustainability_orientation": "high",
            "price_sensitivity": "medium",
            "novelty_seeking": "high",
            "brand_loyalty": "medium",
            "health_concern": "medium",
        },
        "reasoning_policies": {
            "purchase_advice": {
                "default_biases": ["quality first", "eco labels"],
                "tradeoff_rules": ["quality over price", "ethics over convenience"],
            },
            "product_evaluation": {
                "praise_triggers": ["taste", "origin transparency"],
                "criticism_triggers": ["stale beans", "misleading claims"],
            },
        },
        "content_filters": {
            "avoid_styles": ["aggressive marketing"],
            "emphasise_disclaimers_on": ["health claims"],
        },
    }
    (directory / "test-persona.json").write_text(json.dumps(payload), encoding="utf-8")
    return directory


def test_create_group_random_mode(traits_dir: Path, tmp_path: Path):
    generator = GroupGenerator(base_dir=tmp_path / "surveys", traits_dirs=[traits_dir])

    group = generator.create_group(
        composition=[{"persona_id": "test-persona", "count": 3}],
        mode="random",
        seed=42,
    )

    assert group.generation_method == "random"
    assert len(group.respondents) == 3
    assert all(resp.persona_id == "test-persona" for resp in group.respondents)
    assert all(resp.generation_method == "random" for resp in group.respondents)
    assert all(resp.country for resp in group.respondents)
    assert all(resp.gender for resp in group.respondents)
    assert all(resp.ethnicity for resp in group.respondents)

    group_dir = tmp_path / "surveys" / "groups" / group.group_id
    assert (group_dir / "group_info.json").exists()
    assert (group_dir / "profiles").is_dir()
    assert len(list((group_dir / "profiles").glob("*.json"))) == 3
    assert not (tmp_path / "surveys" / "groups" / f"{group.group_id}.json").exists()

    loaded = generator.get_group(group.group_id)
    assert loaded.group_id == group.group_id
    assert len(loaded.respondents) == 3


def test_create_group_persists_optional_group_name(traits_dir: Path, tmp_path: Path):
    generator = GroupGenerator(base_dir=tmp_path / "surveys", traits_dirs=[traits_dir])

    group = generator.create_group(
        composition=[{"persona_id": "test-persona", "count": 1}],
        mode="random",
        group_name="  Espresso Fans Milan  ",
        seed=11,
    )

    assert group.group_name == "Espresso Fans Milan"

    loaded = generator.get_group(group.group_id)
    assert loaded.group_name == "Espresso Fans Milan"


def test_create_group_with_country_filter(traits_dir: Path, tmp_path: Path):
    generator = GroupGenerator(base_dir=tmp_path / "surveys", traits_dirs=[traits_dir])
    group = generator.create_group(
        composition=[{"persona_id": "test-persona", "count": 5}],
        mode="random",
        countries=["france"],
        seed=77,
    )

    assert len(group.respondents) == 5
    assert all(resp.country == "france" for resp in group.respondents)


def test_create_group_rejects_unknown_country(traits_dir: Path, tmp_path: Path):
    generator = GroupGenerator(base_dir=tmp_path / "surveys", traits_dirs=[traits_dir])

    with pytest.raises(ValueError, match="Unknown countries"):
        generator.create_group(
            composition=[{"persona_id": "test-persona", "count": 1}],
            mode="random",
            countries=["nowhere-land"],
        )


def test_create_group_llm_mode_falls_back_to_schema_compatible_profiles(
    traits_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ADSP_LLM_BACKEND", "stub")
    generator = GroupGenerator(base_dir=tmp_path / "surveys", traits_dirs=[traits_dir])

    group = generator.create_group(
        composition=[{"persona_id": "test-persona", "count": 2}],
        mode="llm",
        seed=7,
    )

    assert group.generation_method == "llm"
    assert len(group.respondents) == 2
    assert all(resp.generation_method == "llm" for resp in group.respondents)
    assert all(resp.style_profile for resp in group.respondents)


def test_missing_traits_raises_file_not_found(tmp_path: Path):
    generator = GroupGenerator(base_dir=tmp_path / "surveys", traits_dirs=[tmp_path / "missing"])

    with pytest.raises(FileNotFoundError):
        generator.create_group(composition=[{"persona_id": "unknown", "count": 1}])


def test_get_group_supports_legacy_single_file_format(tmp_path: Path):
    base_dir = tmp_path / "surveys"
    groups_dir = base_dir / "groups"
    groups_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "group_id": "legacy-group",
        "group_name": "Legacy Named Group",
        "created_at": "2026-03-08T00:00:00+00:00",
        "composition": [{"persona_id": "test-persona", "count": 1}],
        "respondents": [
            {
                "respondent_id": "legacy-resp-00001",
                "persona_id": "test-persona",
                "name": "Legacy User",
                "key_indicators": [],
                "style_profile": {},
                "value_frame": {},
                "reasoning_policies": {},
                "content_filters": {},
                "generation_method": "random",
                "seed": 1,
                "created_at": "2026-03-08T00:00:00+00:00",
            }
        ],
        "generation_method": "random",
    }
    (groups_dir / "legacy-group.json").write_text(json.dumps(payload), encoding="utf-8")

    generator = GroupGenerator(base_dir=base_dir, traits_dirs=[tmp_path / "unused"])
    group = generator.get_group("legacy-group")

    assert group.group_id == "legacy-group"
    assert group.group_name == "Legacy Named Group"
    assert len(group.respondents) == 1
