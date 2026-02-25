"""Utilities for stable persona hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger


def compute_persona_hashes(personas_map: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """Compute stable hashes for all personas keyed by persona_id."""
    return {
        persona_id: compute_persona_hash(persona)
        for persona_id, persona in personas_map.items()
    }


def compute_persona_hash(persona: Dict[str, Any]) -> str:
    """Compute stable content hash for a persona, excluding runtime hash flags."""
    sanitized = _deep_copy_json(persona)
    sanitized.pop("persona_hash", None)
    sanitized.pop("reasoned_for_hash", None)
    sanitized.pop("reasoned_hash", None)
    serialized = json.dumps(sanitized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def write_personas_map_bundle(
    path: Path,
    personas_map: Dict[str, Dict[str, Any]],
    persona_hashes: Dict[str, str],
    *,
    general_content: Any,
    pages: Any,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "personas": list(personas_map.values()),
        "personas_map": personas_map,
        "persona_hashes": persona_hashes,
        "general_content": general_content,
        "pages": pages,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote persona bundle with hashes to {path}")


def load_existing_persona_bundle(path: Path) -> tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    if not path.exists():
        return {}, {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        logger.warning(f"Failed to load existing persona bundle from {path}: {exc}")
        return {}, {}

    if not isinstance(payload, dict):
        return {}, {}

    personas_map = _coerce_personas_map(payload)
    old_hashes_raw = payload.get("persona_hashes")
    old_hashes: Dict[str, str] = {}
    if isinstance(old_hashes_raw, dict):
        for persona_id, hash_value in old_hashes_raw.items():
            if isinstance(hash_value, str) and hash_value:
                old_hashes[str(persona_id)] = hash_value
    if not old_hashes and personas_map:
        old_hashes = compute_persona_hashes(personas_map)

    return personas_map, old_hashes


def merge_persona_maps(
    existing: Dict[str, Dict[str, Any]],
    incoming: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for persona_id, persona in existing.items():
        if not isinstance(persona, dict):
            continue
        normalized = _deep_copy_json(persona)
        normalized["persona_id"] = persona_id
        merged[persona_id] = deduplicate_indicators(normalized)

    for persona_id, persona in incoming.items():
        if not isinstance(persona, dict):
            continue
        normalized_id = str(persona.get("persona_id") or persona_id).strip() or str(persona_id)
        normalized_incoming = deduplicate_indicators(_deep_copy_json(persona))
        normalized_incoming["persona_id"] = normalized_id

        if normalized_id not in merged:
            merged[normalized_id] = normalized_incoming
            continue

        merged[normalized_id] = deduplicate_indicators(
            _deep_merge_payload(merged[normalized_id], normalized_incoming)
        )

    return merged


def deduplicate_indicators(persona: Dict[str, Any]) -> Dict[str, Any]:
    result = _deep_copy_json(persona)
    indicators = result.get("indicators")
    if isinstance(indicators, list):
        result["indicators"] = _merge_indicators(indicators, [])
    return result


def select_personas_with_changed_hashes(
    personas_map: Dict[str, Dict[str, Any]],
    new_hashes: Dict[str, str],
    old_hashes: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    if not new_hashes:
        return personas_map
    changed: Dict[str, Dict[str, Any]] = {}
    for persona_id, persona in personas_map.items():
        if new_hashes.get(persona_id) != old_hashes.get(persona_id):
            changed[persona_id] = persona
    return changed


def _coerce_personas_map(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    personas_map: Dict[str, Dict[str, Any]] = {}

    raw_map = payload.get("personas_map")
    if isinstance(raw_map, dict):
        for persona_id, persona in raw_map.items():
            if not isinstance(persona, dict):
                continue
            normalized_id = str(persona.get("persona_id") or persona_id).strip() or str(persona_id)
            normalized = _deep_copy_json(persona)
            normalized["persona_id"] = normalized_id
            personas_map[normalized_id] = deduplicate_indicators(normalized)
        return personas_map

    raw_personas = payload.get("personas")
    if not isinstance(raw_personas, list):
        return personas_map
    for index, persona in enumerate(raw_personas, start=1):
        if not isinstance(persona, dict):
            continue
        persona_id = str(persona.get("persona_id") or f"persona-{index}").strip()
        if not persona_id:
            continue
        normalized = _deep_copy_json(persona)
        normalized["persona_id"] = persona_id
        personas_map[persona_id] = deduplicate_indicators(normalized)
    return personas_map


def _deep_merge_payload(
    base: Dict[str, Any],
    incoming: Dict[str, Any],
) -> Dict[str, Any]:
    result = _deep_copy_json(base)
    for key, incoming_value in incoming.items():
        if key not in result:
            result[key] = _deep_copy_json(incoming_value)
            continue

        existing_value = result.get(key)
        if isinstance(existing_value, dict) and isinstance(incoming_value, dict):
            result[key] = _deep_merge_payload(existing_value, incoming_value)
            continue

        if isinstance(existing_value, list) and isinstance(incoming_value, list):
            if key == "indicators":
                result[key] = _merge_indicators(existing_value, incoming_value)
            else:
                result[key] = _merge_list_values(existing_value, incoming_value)
            continue

        if incoming_value not in (None, "", [], {}):
            result[key] = _deep_copy_json(incoming_value)
    return result


def _merge_indicators(existing: List[Any], incoming: List[Any]) -> List[Any]:
    merged: List[Any] = []
    by_id: Dict[str, Dict[str, Any]] = {}
    by_id_index: Dict[str, int] = {}
    seen_without_id: set[str] = set()

    def handle(raw_indicator: Any) -> None:
        if not isinstance(raw_indicator, dict):
            marker = _stable_marker(raw_indicator)
            if marker in seen_without_id:
                return
            seen_without_id.add(marker)
            merged.append(_deep_copy_json(raw_indicator))
            return

        indicator = _deep_copy_json(raw_indicator)
        indicator_id = _indicator_id(indicator)
        if indicator_id and indicator_id in by_id:
            merged_indicator = _deep_merge_payload(by_id[indicator_id], indicator)
            by_id[indicator_id] = merged_indicator
            merged[by_id_index[indicator_id]] = merged_indicator
            return

        if not indicator_id:
            marker = _stable_marker(indicator)
            if marker in seen_without_id:
                return
            seen_without_id.add(marker)

        merged.append(indicator)
        if indicator_id:
            by_id[indicator_id] = indicator
            by_id_index[indicator_id] = len(merged) - 1

    for item in existing:
        handle(item)
    for item in incoming:
        handle(item)

    return merged


def _indicator_id(indicator: Dict[str, Any]) -> str:
    raw_id = indicator.get("id") or indicator.get("indicator_id")
    if raw_id is None:
        return ""
    return str(raw_id).strip()


def _merge_list_values(existing: List[Any], incoming: List[Any]) -> List[Any]:
    merged: List[Any] = []
    seen: set[str] = set()
    for item in [*existing, *incoming]:
        marker = _stable_marker(item)
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(_deep_copy_json(item))
    return merged


def _stable_marker(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except TypeError:
        return repr(value)


def _deep_copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))
