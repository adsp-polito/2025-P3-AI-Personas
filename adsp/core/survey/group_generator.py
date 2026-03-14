"""Respondent group generation for survey simulation."""

from __future__ import annotations

import copy
import os
from pathlib import Path
import random
import shutil
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from loguru import logger

from adsp.config import PROCESSED_DATA_DIR

from .models import PersonaConfig, RespondentGroup, RespondentProfile
from .utils import (
    ensure_dir,
    load_json,
    make_identifier,
    model_dump,
    save_json,
    utc_now,
)
from .validators import validate_group, validate_group_composition, validate_respondent_profile

try:
    from faker import Faker
except Exception:  # pragma: no cover
    Faker = None  # type: ignore[assignment]

_FORMALITY_LEVELS = ["formal", "medium", "casual"]
_DIRECTNESS_LEVELS = ["direct", "balanced", "indirect"]
_EMOTIONAL_LEVELS = ["enthusiastic", "neutral", "reserved"]
_CRITICALITY_LEVELS = ["high", "medium", "low"]
_VERBOSITY_LEVELS = ["detailed", "balanced", "concise"]
_LOW_MED_HIGH = ["low", "medium", "high"]

_COUNTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "italy": {
        "display_name": "Italy",
        "description": "Italian respondents and naming locale.",
        "faker_locale": "it_IT",
        "ethnicities": ["Italian", "Mediterranean", "North African", "Eastern European", "Mixed"],
    },
    "france": {
        "display_name": "France",
        "description": "French respondents and naming locale.",
        "faker_locale": "fr_FR",
        "ethnicities": ["French", "North African", "Sub-Saharan African", "European", "Mixed"],
    },
    "united_states": {
        "display_name": "United States",
        "description": "US respondents and naming locale.",
        "faker_locale": "en_US",
        "ethnicities": ["White American", "Black American", "Hispanic/Latino", "Asian American", "Mixed"],
    },
    "united_kingdom": {
        "display_name": "United Kingdom",
        "description": "UK respondents and naming locale.",
        "faker_locale": "en_GB",
        "ethnicities": ["White British", "Black British", "British Asian", "Middle Eastern British", "Mixed"],
    },
    "spain": {
        "display_name": "Spain",
        "description": "Spanish respondents and naming locale.",
        "faker_locale": "es_ES",
        "ethnicities": ["Spanish", "Latin American", "North African", "Roma", "Mixed"],
    },
    "germany": {
        "display_name": "Germany",
        "description": "German respondents and naming locale.",
        "faker_locale": "de_DE",
        "ethnicities": ["German", "Turkish German", "Eastern European", "Middle Eastern", "Mixed"],
    },
    "vietnam": {
        "display_name": "Vietnam",
        "description": "Vietnamese respondents and naming locale.",
        "faker_locale": "vi_VN",
        "ethnicities": ["Kinh", "Tay", "Thai", "Hoa", "Mixed"],
    },
}


class GroupGenerator:
    """Creates respondent groups from persona trait files."""

    def __init__(
        self,
        base_dir: Path | None = None,
        traits_dirs: Sequence[Path] | None = None,
    ) -> None:
        self.base_dir = Path(base_dir or (PROCESSED_DATA_DIR / "surveys"))
        self.groups_dir = ensure_dir(self.base_dir / "groups")
        self._traits_dirs = self._resolve_traits_dirs(traits_dirs)

    def create_group(
        self,
        composition: Iterable[Mapping[str, Any]],
        mode: str = "random",
        **options: Any,
    ) -> RespondentGroup:
        mode_normalized = (mode or "random").strip().lower()
        if mode_normalized not in {"random", "llm"}:
            raise ValueError("mode must be one of: random, llm")

        configs: List[PersonaConfig] = validate_group_composition(composition)
        sampling_ratio = float(options.get("sampling_ratio", 0.7))
        include_names = bool(options.get("include_names", True))
        countries = self._normalize_country_list(options.get("countries"))
        requested_seed = options.get("seed")
        base_seed = int(requested_seed) if requested_seed is not None else random.randint(1, 2_147_483_647)
        rng = random.Random(base_seed)

        group_id = str(options.get("group_id") or make_identifier("group", rng=rng))
        group_name = self._normalize_group_name(options.get("group_name"))
        respondents: List[RespondentProfile] = []

        for config in configs:
            traits = self._load_traits(config.persona_id)
            for _ in range(config.count):
                respondent_seed = rng.randint(1, 2_147_483_647)
                respondent_id = f"{group_id}-resp-{len(respondents) + 1:05d}"
                generation_method = "llm" if mode_normalized == "llm" else "random"
                profile = self.generate_profile_random(
                    persona_id=config.persona_id,
                    seed=respondent_seed,
                    respondent_id=respondent_id,
                    traits=traits,
                    sampling_ratio=sampling_ratio,
                    include_names=include_names,
                    countries=countries,
                    generation_method=generation_method,
                )
                respondents.append(profile)

        group = RespondentGroup(
            group_id=group_id,
            group_name=group_name,
            created_at=utc_now(),
            composition=configs,
            respondents=respondents,
            generation_method=mode_normalized,
        )
        self._write_group(group)
        return group

    def generate_profile_random(
        self,
        persona_id: str,
        seed: int,
        *,
        respondent_id: str | None = None,
        traits: Mapping[str, Any] | None = None,
        sampling_ratio: float = 0.7,
        include_names: bool = True,
        countries: Sequence[str] | None = None,
        generation_method: str = "random",
    ) -> RespondentProfile:
        rng = random.Random(int(seed))
        source = dict(traits) if traits is not None else self._load_traits(persona_id)

        key_indicators = self._sample_key_indicators(source.get("key_indicators") or [], sampling_ratio, rng)
        style_profile = self._sample_style_profile(source.get("style_profile") or {}, rng)
        value_frame = self._sample_value_frame(source.get("value_frame") or {}, rng)
        reasoning_policies = self._sample_reasoning_policies(source.get("reasoning_policies") or {}, rng)
        content_filters = copy.deepcopy(source.get("content_filters") or {})

        profile_id = respondent_id or make_identifier("resp", rng=rng)
        available_countries = list(countries) if countries else list(_COUNTRY_PROFILES.keys())
        country = rng.choice(available_countries)
        gender = self._sample_gender(rng)
        ethnicity = self._sample_ethnicity(country, rng)
        if include_names:
            name = self.generate_name(country=country, gender=gender, rng=rng)
        else:
            name = profile_id

        payload = {
            "respondent_id": profile_id,
            "persona_id": persona_id,
            "name": name,
            "country": country,
            "gender": gender,
            "ethnicity": ethnicity,
            "key_indicators": key_indicators,
            "style_profile": style_profile,
            "value_frame": value_frame,
            "reasoning_policies": reasoning_policies,
            "content_filters": content_filters,
            "generation_method": generation_method,
            "seed": int(seed),
            "created_at": utc_now(),
        }
        return validate_respondent_profile(payload)

    def generate_name(
        self,
        *,
        country: str,
        gender: str,
        rng: random.Random | None = None,
    ) -> str:
        local_rng = rng or random.Random()
        profile = _COUNTRY_PROFILES.get(country, _COUNTRY_PROFILES["united_states"])
        faker_locale = str(profile.get("faker_locale", "en_US"))

        if Faker is None:
            return make_identifier("name", rng=local_rng)

        try:
            fake = Faker(faker_locale)
            fake.seed_instance(local_rng.randint(1, 2_147_483_647))
            if gender == "female" and hasattr(fake, "first_name_female"):
                first = str(fake.first_name_female())
            elif gender == "male" and hasattr(fake, "first_name_male"):
                first = str(fake.first_name_male())
            else:
                first = str(fake.first_name())
            return f"{first} {fake.last_name()}"
        except Exception:
            logger.debug("Faker name generation failed for country={} locale={}", country, faker_locale)
            return make_identifier("name", rng=local_rng)

    @staticmethod
    def list_available_countries() -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        for country_id in sorted(_COUNTRY_PROFILES.keys()):
            profile = _COUNTRY_PROFILES[country_id]
            items.append(
                {
                    "country_id": country_id,
                    "display_name": str(profile.get("display_name", country_id)),
                    "description": str(profile.get("description", "")),
                }
            )
        return items

    def get_group(self, group_id: str) -> RespondentGroup:
        info_path = self._group_info_path(group_id)
        if info_path.exists():
            info_payload = load_json(info_path)
            profiles_payload: List[Dict[str, Any]] = []
            for profile_path in sorted(self._profiles_dir(group_id).glob("*.json")):
                profile_payload = load_json(profile_path)
                if isinstance(profile_payload, dict):
                    profiles_payload.append(profile_payload)

            if isinstance(info_payload, dict):
                payload = dict(info_payload)
                payload["respondents"] = profiles_payload
                return validate_group(payload)

        legacy_path = self._legacy_group_path(group_id)
        if legacy_path.exists():
            return validate_group(load_json(legacy_path))

        raise KeyError(f"Group '{group_id}' not found")

    def list_groups(self) -> List[RespondentGroup]:
        groups: List[RespondentGroup] = []
        seen: set[str] = set()

        for path in sorted(self.groups_dir.iterdir()):
            if not path.is_dir():
                continue
            group_id = path.name
            try:
                groups.append(self.get_group(group_id))
                seen.add(group_id)
            except Exception as exc:
                logger.warning("Skipping invalid group directory {}: {}", path, exc)

        for path in sorted(self.groups_dir.glob("*.json")):
            group_id = path.stem
            if group_id in seen:
                continue
            try:
                groups.append(validate_group(load_json(path)))
            except Exception as exc:
                logger.warning("Skipping invalid group file {}: {}", path, exc)
        return groups

    def _write_group(self, group: RespondentGroup) -> None:
        group_dir = self._group_dir(group.group_id)
        if group_dir.exists():
            shutil.rmtree(group_dir)
        profiles_dir = ensure_dir(group_dir / "profiles")

        payload = model_dump(group)
        respondents = payload.pop("respondents", [])
        save_json(group_dir / "group_info.json", payload)

        for profile in respondents:
            respondent_id = str(profile.get("respondent_id", "")).strip()
            if not respondent_id:
                continue
            save_json(profiles_dir / f"{respondent_id}.json", profile)

    def _group_dir(self, group_id: str) -> Path:
        return self.groups_dir / group_id

    def _group_info_path(self, group_id: str) -> Path:
        return self._group_dir(group_id) / "group_info.json"

    def _profiles_dir(self, group_id: str) -> Path:
        return self._group_dir(group_id) / "profiles"

    def _legacy_group_path(self, group_id: str) -> Path:
        return self.groups_dir / f"{group_id}.json"

    @staticmethod
    def _normalize_group_name(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _load_traits(self, persona_id: str) -> Dict[str, Any]:
        for directory in self._traits_dirs:
            path = directory / f"{persona_id}.json"
            if not path.exists():
                continue
            payload = load_json(path)
            if isinstance(payload, dict):
                return payload

        searched = ", ".join(str(path) for path in self._traits_dirs)
        raise FileNotFoundError(f"Traits file not found for persona '{persona_id}'. Searched: {searched}")

    @staticmethod
    def _resolve_traits_dirs(traits_dirs: Sequence[Path] | None) -> List[Path]:
        if traits_dirs:
            return [Path(path) for path in traits_dirs]

        resolved: List[Path] = []

        env_survey = os.environ.get("ADSP_SURVEY_TRAITS_DIR", "")
        env_persona = os.environ.get("ADSP_PERSONA_TRAITS_DIR", "")

        for raw in (env_survey, env_persona):
            if not raw:
                continue
            for segment in raw.split(os.pathsep):
                segment = segment.strip()
                if segment:
                    resolved.append(Path(segment))

        resolved.extend(
            [
                PROCESSED_DATA_DIR / "personas_" / "common_traits",
                PROCESSED_DATA_DIR / "personas" / "common_traits",
            ]
        )

        deduped: List[Path] = []
        seen: set[str] = set()
        for path in resolved:
            marker = str(path)
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(path)
        return deduped

    def _sample_key_indicators(
        self,
        indicators: Sequence[Mapping[str, Any]],
        sampling_ratio: float,
        rng: random.Random,
    ) -> List[Dict[str, Any]]:
        items = [copy.deepcopy(item) for item in indicators if isinstance(item, Mapping)]
        if not items:
            return []

        ratio = max(0.05, min(1.0, float(sampling_ratio)))
        sample_size = max(1, min(len(items), int(round(len(items) * ratio))))
        selected = rng.sample(items, k=sample_size)

        for indicator in selected:
            metrics = indicator.get("metrics")
            if not isinstance(metrics, list):
                continue
            for metric in metrics:
                if not isinstance(metric, dict):
                    continue
                value = metric.get("value")
                if isinstance(value, (int, float)):
                    jitter = 1.0 + rng.uniform(-0.05, 0.05)
                    candidate = float(value) * jitter
                    metric["value"] = round(candidate, 2)

        return selected

    def _sample_style_profile(self, style_profile: Mapping[str, Any], rng: random.Random) -> Dict[str, Any]:
        style = copy.deepcopy(dict(style_profile))

        tones = [tone for tone in style.get("tone_adjectives", []) if isinstance(tone, str)]
        if tones:
            target = min(len(tones), rng.randint(3, min(5, len(tones))))
            style["tone_adjectives"] = rng.sample(tones, k=target)

        style["formality_level"] = self._maybe_shift(style.get("formality_level"), _FORMALITY_LEVELS, rng)
        style["directness"] = self._maybe_shift(style.get("directness"), _DIRECTNESS_LEVELS, rng)
        style["emotional_flavour"] = self._maybe_shift(style.get("emotional_flavour"), _EMOTIONAL_LEVELS, rng)
        style["criticality_level"] = self._maybe_shift(style.get("criticality_level"), _CRITICALITY_LEVELS, rng)
        style["verbosity_preference"] = self._maybe_shift(style.get("verbosity_preference"), _VERBOSITY_LEVELS, rng)

        return style

    def _sample_value_frame(self, value_frame: Mapping[str, Any], rng: random.Random) -> Dict[str, Any]:
        frame = copy.deepcopy(dict(value_frame))
        priorities = [item for item in frame.get("priority_rank", []) if isinstance(item, str)]
        if priorities:
            if len(priorities) <= 3:
                frame["priority_rank"] = priorities
            else:
                keep = rng.randint(3, min(5, len(priorities)))
                primary = priorities[0]
                tail = priorities[1:]
                rng.shuffle(tail)

                if rng.random() < 0.8:
                    chosen = [primary, *tail[: max(0, keep - 1)]]
                else:
                    shuffled = priorities[:]
                    rng.shuffle(shuffled)
                    chosen = shuffled[:keep]
                frame["priority_rank"] = chosen

        for field in (
            "sustainability_orientation",
            "price_sensitivity",
            "novelty_seeking",
            "brand_loyalty",
            "health_concern",
        ):
            frame[field] = self._maybe_shift(frame.get(field), _LOW_MED_HIGH, rng)
        return frame

    def _sample_reasoning_policies(
        self,
        reasoning_policies: Mapping[str, Any],
        rng: random.Random,
    ) -> Dict[str, Any]:
        policies = copy.deepcopy(dict(reasoning_policies))
        return self._prune_nested_lists(policies, rng)

    def _prune_nested_lists(self, payload: Any, rng: random.Random) -> Any:
        if isinstance(payload, list):
            if len(payload) <= 1:
                return payload
            drop_ratio = rng.uniform(0.1, 0.2)
            drop_count = int(round(len(payload) * drop_ratio))
            keep_count = max(1, len(payload) - drop_count)
            if keep_count >= len(payload):
                return payload
            return rng.sample(payload, keep_count)

        if isinstance(payload, dict):
            return {key: self._prune_nested_lists(value, rng) for key, value in payload.items()}

        return payload

    @staticmethod
    def _maybe_shift(value: Any, levels: List[str], rng: random.Random) -> Any:
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        if normalized not in levels:
            return value
        if rng.random() >= 0.2:
            return normalized

        current = levels.index(normalized)
        direction = rng.choice([-1, 1])
        candidate = max(0, min(len(levels) - 1, current + direction))
        return levels[candidate]

    @staticmethod
    def _sample_gender(rng: random.Random) -> str:
        return rng.choices(["female", "male"], k=1)[0]

    @staticmethod
    def _sample_ethnicity(country: str, rng: random.Random) -> str:
        profile = _COUNTRY_PROFILES.get(country, _COUNTRY_PROFILES["united_states"])
        choices = [str(item) for item in profile.get("ethnicities", []) if str(item).strip()]
        if not choices:
            return "Mixed"
        return rng.choice(choices)

    def _normalize_country_list(self, value: Any) -> List[str] | None:
        if value is None:
            return None
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise ValueError("countries must be a list of country ids or names")

        resolved: List[str] = []
        unknown: List[str] = []
        seen: set[str] = set()
        for item in value:
            candidate = str(item or "").strip().lower().replace("-", "_").replace(" ", "_")
            if candidate not in _COUNTRY_PROFILES:
                unknown.append(str(item))
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            resolved.append(candidate)

        if unknown:
            supported = ", ".join(sorted(_COUNTRY_PROFILES.keys()))
            raise ValueError(f"Unknown countries: {', '.join(unknown)}. Supported values: {supported}")
        if not resolved:
            raise ValueError("countries must contain at least one supported country")
        return resolved
