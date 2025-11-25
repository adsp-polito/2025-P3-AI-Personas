"""Configuration for the persona extraction pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from adsp import config


@dataclass
class PersonaExtractionConfig:
    pdf_path: Path = config.DATA_DIR / "raw" / "lavazza" / "customer-segmentation" / (
        "2023 03_FR_Consumers Segmentation France.pdf"
    )
    page_images_dir: Path = (
        config.INTERIM_DATA_DIR / "persona_extraction" / "page_images"
    )
    raw_responses_dir: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "pages"
    merged_output_path: Path = config.PROCESSED_DATA_DIR / "personas" / "personas.json"
    qa_report_path: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "qa_report.json"
    debug: bool = False
    debug_dir: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "debug"
    reuse_cache: bool = True

    vllm_base_url: str = field(
        default_factory=lambda: os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    )
    vllm_model: str = field(default_factory=lambda: os.environ.get("VLLM_MODEL", ""))
    vllm_api_key: str = field(default_factory=lambda: os.environ.get("VLLM_API_KEY", "EMPTY"))
    temperature: float = 0.0
    top_p: float = 0.01
    max_tokens: int = 4000
    response_timeout: float = 300.0
    max_concurrent_requests: int = 1
    max_retries: int = 1
    backoff_seconds: float = 1.5
    dpi: int = 300
    page_range: Optional[tuple[int, int]] = None  # inclusive 1-based page range
    merge_strategy: Dict[str, str] = field(
        default_factory=dict
    )  # dotted path -> fill|overwrite|append
