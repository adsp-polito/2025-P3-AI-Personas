"""CLI entrypoint to run the persona extraction pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger

from adsp.data_pipeline.persona_data_pipeline import (
    PersonaExtractionConfig,
    run_persona_extraction_pipeline,
)


def parse_page_range(raw: str) -> Tuple[int, int]:
    try:
        start_str, end_str = raw.split(",")
        start = int(start_str)
        end = int(end_str)
        if start < 1 or end < start:
            raise ValueError
        return start, end
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            "Page range must be 'start,end' with 1-based inclusive bounds."
        ) from exc


def build_config(args: argparse.Namespace) -> PersonaExtractionConfig:
    cfg = PersonaExtractionConfig()
    cfg.pdf_path = Path(args.pdf_path)
    cfg.page_range = args.page_range
    cfg.debug = args.debug
    cfg.vllm_base_url = args.vllm_base_url
    cfg.vllm_model = args.vllm_model
    cfg.vllm_api_key = args.vllm_api_key
    cfg.temperature = args.temperature
    cfg.top_p = args.top_p
    cfg.max_tokens = args.max_tokens
    cfg.response_timeout = args.response_timeout
    cfg.max_concurrent_requests = args.concurrency
    cfg.max_retries = args.max_retries
    cfg.backoff_seconds = args.backoff
    cfg.dpi = args.dpi
    cfg.page_images_dir = Path(args.page_images_dir)
    cfg.raw_responses_dir = Path(args.raw_responses_dir)
    cfg.reuse_cache = args.reuse_cache
    cfg.merged_output_path = Path(args.merged_output_path)
    cfg.persona_output_dir = Path(args.persona_output_dir)
    cfg.qa_report_path = Path(args.qa_report_path)
    cfg.structured_pages_output_path = Path(args.structured_pages_output_path)
    cfg.context_window = args.context_window
    return cfg


def main(raw_args: Optional[list[str]] = None) -> None:
    default_cfg = PersonaExtractionConfig()
    parser = argparse.ArgumentParser(description="Run persona extraction pipeline.")
    parser.add_argument(
        "--pdf-path",
        type=str,
        default=str(default_cfg.pdf_path),
        help="Path to PDF to process.",
    )
    parser.add_argument(
        "--page-range",
        type=parse_page_range,
        default=default_cfg.page_range,
        help="Inclusive page range 'start,end' (1-based).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=default_cfg.debug,
        help="Enable debug mode to store raw model responses in a debug folder.",
    )
    parser.add_argument(
        "--vllm-base-url",
        type=str,
        default=default_cfg.vllm_base_url,
        help="OpenAI-compatible base URL.",
    )
    parser.add_argument(
        "--vllm-model",
        type=str,
        default=default_cfg.vllm_model,
        help="Vision model name.",
    )
    parser.add_argument(
        "--vllm-api-key",
        type=str,
        default=default_cfg.vllm_api_key,
        help="API key (can be dummy).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=default_cfg.temperature,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=default_cfg.top_p,
        help="Top-p nucleus sampling value.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=default_cfg.max_tokens,
        help="Max tokens for response.",
    )
    parser.add_argument(
        "--response-timeout",
        type=float,
        default=default_cfg.response_timeout,
        help="HTTP timeout (seconds) for model response.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=default_cfg.max_concurrent_requests,
        help="Max concurrent requests.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=default_cfg.max_retries,
        help="Max retries on failure.",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=default_cfg.backoff_seconds,
        help="Backoff seconds between retries.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=default_cfg.dpi,
        help="Render DPI for page images.",
    )
    parser.add_argument(
        "--page-images-dir",
        type=str,
        default=str(default_cfg.page_images_dir),
        help="Dir to store rendered pages.",
    )
    parser.add_argument(
        "--no-cache",
        dest="reuse_cache",
        action="store_false",
        default=default_cfg.reuse_cache,
        help="Ignore cached page responses and force re-extraction.",
    )
    parser.add_argument(
        "--raw-responses-dir",
        type=str,
        default=str(default_cfg.raw_responses_dir),
        help="Dir to store raw responses.",
    )
    parser.add_argument(
        "--merged-output-path",
        type=str,
        default=str(default_cfg.merged_output_path),
        help="Merged personas output path.",
    )
    parser.add_argument(
        "--persona-output-dir",
        type=str,
        default=str(default_cfg.persona_output_dir),
        help="Directory to store individual persona JSON files.",
    )
    parser.add_argument(
        "--qa-report-path",
        type=str,
        default=str(default_cfg.qa_report_path),
        help="QA report output path.",
    )
    parser.add_argument(
        "--structured-pages-output-path",
        type=str,
        default=str(default_cfg.structured_pages_output_path),
        help="Where to store structured page-level JSON output.",
    )
    parser.add_argument(
        "--context-window",
        type=int,
        default=default_cfg.context_window,
        help="Number of adjacent pages to send alongside each primary page for context.",
    )
    args = parser.parse_args(raw_args)

    config = build_config(args)
    logger.info("Prepared persona extraction configuration.")
    logger.info(f"Using PDF: {config.pdf_path}")
    logger.info(f"Model: {config.vllm_model} @ {config.vllm_base_url}")
    if config.page_range:
        logger.info(f"Page range: {config.page_range}")
    if config.reuse_cache:
        cache_files = (
            list(config.raw_responses_dir.glob("page_*.json"))
            if config.raw_responses_dir.exists()
            else []
        )
        logger.info(
            f"Cache reuse enabled; {len(cache_files)} cached page files available in "
            f"{config.raw_responses_dir}"
        )
    else:
        logger.info("Cache reuse disabled; existing cached pages will be ignored.")

    logger.info("Starting persona extraction run...")
    result = run_persona_extraction_pipeline(config)
    logger.info("Persona extraction pipeline finished.")
    personas = result.get("personas", [])
    persona_ids = [p.get("persona_id") for p in personas if isinstance(p, dict)]
    logger.info(f"Personas extracted: {persona_ids}")
    summary = {
        "persona_ids": persona_ids,
        "pages_processed": [r.page_number for r in result["page_results"]],
        "pages_with_persona": [
            r.page_number
            for r in result["page_results"]
            if r.parsed and isinstance(r.parsed.get("personas"), list) and r.parsed.get("personas")
        ],
        "output_path": str(config.merged_output_path),
        "qa_report_path": str(config.qa_report_path),
        "structured_pages_output_path": str(config.structured_pages_output_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
