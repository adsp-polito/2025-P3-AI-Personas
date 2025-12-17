"""Configuration for the fact data extraction pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from adsp import config


@dataclass
class FactDataExtractionConfig:
    # define default values
    pdf_path: Path = config.DATA_DIR / "raw" / "lavazza" / "customer-segmentation" / (
        "2023 03_FR_Consumers Segmentation France.pdf"
    )
    page_images_dir: Path = (
        config.INTERIM_DATA_DIR / "fact_data_extraction" / "page_images"
    )
    raw_responses_dir: Path = config.INTERIM_DATA_DIR / "fact_data_extraction" / "pages"
    fact_data_output_dir: Path = config.PROCESSED_DATA_DIR / "fact_data"
    qa_report_path: Path = config.INTERIM_DATA_DIR / "fact_data_extraction" / "qa_report.json"
    debug: bool = False
    debug_dir: Path = config.INTERIM_DATA_DIR / "fact_data_extraction" / "debug"
    reuse_cache: bool = True
    structured_pages_output_path: Path = (
        config.INTERIM_DATA_DIR / "fact_data_extraction" / "pages_structured.json"
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