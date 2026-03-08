"""Shared helpers for survey simulation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import random
from typing import Any
import uuid


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp_path = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def model_dump(model: Any) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


def make_identifier(prefix: str, rng: random.Random | None = None) -> str:
    if rng is not None:
        token = "".join(rng.choice("0123456789abcdef") for _ in range(10))
        return f"{prefix}-{token}"
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def parse_json_block(text: str) -> Any:
    cleaned = (text or "").strip()
    if not cleaned:
        return None

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    candidates = [cleaned]
    if "{" in cleaned and "}" in cleaned:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if end > start:
            candidates.append(cleaned[start : end + 1])
    if "[" in cleaned and "]" in cleaned:
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if end > start:
            candidates.append(cleaned[start : end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None
