"""Helpers for loading persona extraction outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Union

from adsp.data_pipeline.schema import PersonaProfileModel


def load_personas_bundle(path: Union[str, Path]) -> List[PersonaProfileModel]:
    """Load `data/processed/personas/personas.json` into typed persona models."""

    json_path = Path(path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    personas = payload.get("personas") if isinstance(payload, dict) else None
    if not isinstance(personas, list):
        return []
    return [PersonaProfileModel(**p) for p in personas if isinstance(p, dict)]


def load_individual_personas(directory: Union[str, Path]) -> Dict[str, PersonaProfileModel]:
    """Load `data/processed/personas/individual/*.json` into a persona_id -> model map."""

    dir_path = Path(directory)
    results: Dict[str, PersonaProfileModel] = {}
    for path in sorted(dir_path.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        persona_id = payload.get("persona_id") or path.stem
        payload["persona_id"] = persona_id
        results[persona_id] = PersonaProfileModel(**payload)
    return results


__all__ = ["load_personas_bundle", "load_individual_personas"]

