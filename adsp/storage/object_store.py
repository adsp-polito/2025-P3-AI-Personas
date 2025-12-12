"""Object storage shim."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

_STORE: Dict[str, Dict[str, bytes]] = {}


def put(bucket: str, file_path: Path) -> None:
    _STORE.setdefault(bucket, {})[file_path.name] = file_path.read_bytes()


def get(bucket: str, key: str) -> bytes:
    return _STORE[bucket][key]


def put_bytes(bucket: str, key: str, payload: bytes) -> None:
    _STORE.setdefault(bucket, {})[key] = payload


def list_keys(bucket: str) -> list[str]:
    return sorted(_STORE.get(bucket, {}).keys())
