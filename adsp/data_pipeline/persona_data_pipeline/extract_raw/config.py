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
    persona_output_dir: Path = config.PROCESSED_DATA_DIR / "personas" / "individual"
    reasoning_output_dir: Path = config.PROCESSED_DATA_DIR / "personas" / "common_traits"
    qa_report_path: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "qa_report.json"
    debug: bool = False
    debug_dir: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "debug"
    reuse_cache: bool = True
    structured_pages_output_path: Path = (
        config.INTERIM_DATA_DIR / "persona_extraction" / "pages_structured.json"
    )
    context_window: int = 1  # number of adjacent pages on each side to include for context

    vllm_base_url: str = field(
        default_factory=lambda: os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    )
    vllm_model: str = field(default_factory=lambda: os.environ.get("VLLM_MODEL", ""))
    vllm_api_key: str = field(default_factory=lambda: os.environ.get("VLLM_API_KEY", "EMPTY"))
    temperature: float = 0.0
    top_p: float = 0.01
    max_tokens: int = 100000
    response_timeout: float = 300.0
    max_concurrent_requests: int = 1
    max_retries: int = 1  # number of retries after the first attempt
    backoff_seconds: float = 1.5
    dpi: int = 300
    page_range: Optional[tuple[int, int]] = None  # inclusive 1-based page range
    merge_strategy: Dict[str, str] = field(
        default_factory=dict
    )  # dotted path -> fill|overwrite|append
    max_image_bytes: int = 10 * 1024 * 1024  # compress images to stay below payload limits
    generate_reasoning_profiles: bool = True
    reasoning_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "REASONING_BASE_URL", os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
        )
    )
    reasoning_model: str = field(default_factory=lambda: os.environ.get("REASONING_MODEL", ""))
    reasoning_api_key: str = field(
        default_factory=lambda: os.environ.get("REASONING_API_KEY", os.environ.get("VLLM_API_KEY", "EMPTY"))
    )
    reasoning_temperature: float = 0.0
    reasoning_top_p: float = 0.01
    reasoning_max_tokens: int = 100000
    reasoning_max_input_chars: int = 100000
    reasoning_max_concurrent: int = 2
