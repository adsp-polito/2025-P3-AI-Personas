"""Utility helpers for fact data extraction."""

from __future__ import annotations

import base64
import hashlib
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


def strip_json_markdown(text: str) -> str:
    """Extract JSON content from possible markdown fences."""
    if "```" not in text:
        return text.strip()
    blocks: List[str] = []
    for part in text.split("```"):
        cleaned = part.strip()
        if not cleaned:
            continue
        if cleaned.startswith("json"):
            cleaned = cleaned[len("json") :].strip()
        blocks.append(cleaned)
    for block in blocks:
        if block.startswith("{") or block.startswith("["):
            return block
    if blocks:
        return max(blocks, key=len)
    return text.strip()


def fast_file_hash(
    file_path: Path,
    *,
    sample_size: int = 1024 * 1024,
    digest_size: int = 8,
) -> str:
    """Compute a fast content hash by sampling first/middle/last file regions.

    The hash includes file size and sampled bytes. For small files, all bytes
    are hashed.
    """
    if sample_size <= 0:
        raise ValueError("sample_size must be > 0")
    if digest_size <= 0:
        raise ValueError("digest_size must be > 0")

    file_size = file_path.stat().st_size
    hasher = hashlib.blake2b(digest_size=digest_size)
    hasher.update(str(file_size).encode("utf-8"))

    with file_path.open("rb") as handle:
        if file_size <= sample_size * 3:
            while True:
                chunk = handle.read(sample_size)
                if not chunk:
                    break
                hasher.update(chunk)
        else:
            # First sample
            hasher.update(handle.read(sample_size))

            # Middle sample
            middle_offset = max(0, (file_size // 2) - (sample_size // 2))
            handle.seek(middle_offset)
            hasher.update(handle.read(sample_size))

            # Tail sample
            tail_offset = max(0, file_size - sample_size)
            handle.seek(tail_offset)
            hasher.update(handle.read(sample_size))

    return hasher.hexdigest()


def encode_image_base64(image_path: Path, max_bytes: Optional[int] = None) -> Tuple[str, str]:
    """
    Encode an image to base64, compressing to JPEG if the PNG exceeds max_bytes.

    Returns:
        (base64_string, mime_type)
    """
    raw = image_path.read_bytes()
    mime = "image/png"
    if max_bytes is None or len(raw) <= max_bytes:
        return base64.b64encode(raw).decode("utf-8"), mime

    try:
        from PIL import Image  # type: ignore

        img = Image.open(image_path).convert("RGB")
        quality_candidates = [85, 75, 65, 55, 45, 35]
        best_data = raw
        best_mime = mime

        for quality in quality_candidates:
            buffer = BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=quality)
            data = buffer.getvalue()
            if len(data) < len(best_data):
                best_data, best_mime = data, "image/jpeg"
            if max_bytes and len(data) <= max_bytes:
                best_data, best_mime = data, "image/jpeg"
                break

        if max_bytes and len(best_data) > max_bytes:
            # Gradually downscale if quality tweaks are insufficient.
            scale = 0.9
            while len(best_data) > max_bytes and scale >= 0.4:
                buffer = BytesIO()
                new_width = max(1, int(img.width * scale))
                new_height = max(1, int(img.height * scale))
                resized = img.resize((new_width, new_height), Image.LANCZOS)
                resized.save(buffer, format="JPEG", optimize=True, quality=65)
                data = buffer.getvalue()
                if len(data) < len(best_data):
                    best_data, best_mime = data, "image/jpeg"
                if len(best_data) <= max_bytes:
                    break
                scale -= 0.1

        logger.debug(
            f"Compressed image {image_path.name} from {len(raw)} to {len(best_data)} bytes (mime={best_mime})"
        )
        return base64.b64encode(best_data).decode("utf-8"), best_mime
    except Exception as exc:  # pragma: no cover - compression guardrail
        logger.warning(f"Falling back to raw image for {image_path.name}: {exc}")
        return base64.b64encode(raw).decode("utf-8"), mime
