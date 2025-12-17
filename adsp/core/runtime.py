"""Helpers to build a runnable local system configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

from adsp.config import PROCESSED_DATA_DIR
from adsp.core.orchestrator import Orchestrator
from adsp.core.persona_registry import PersonaRegistry
from adsp.core.prompt_builder import PromptBuilder
from adsp.core.rag import RAGPipeline
from adsp.core.rag.fact_data_index import FactDataRAGIndex, build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import PersonaRAGIndex
from adsp.data_pipeline.schema import PersonaProfileModel


def resolve_persona_paths(
    processed_dir: Path = PROCESSED_DATA_DIR,
) -> Tuple[Path, Path]:
    """Return (individual_dir, traits_dir) based on defaults + env overrides."""

    individual_dir = Path(
        os.environ.get(
            "ADSP_PERSONAS_DIR",
            str(processed_dir / "personas" / "individual"),
        )
    )
    traits_dir = Path(
        os.environ.get(
            "ADSP_PERSONA_TRAITS_DIR",
            str(processed_dir / "personas" / "common_traits"),
        )
    )
    return individual_dir, traits_dir


def load_personas_from_disk(
    individual_dir: Path,
    *,
    traits_dir: Optional[Path] = None,
) -> List[PersonaProfileModel]:
    """Load persona profiles and optional reasoning traits from disk."""

    personas: List[PersonaProfileModel] = []
    traits_dir = traits_dir if traits_dir and traits_dir.exists() else None

    if not individual_dir.exists():
        logger.warning(f"Persona directory does not exist: {individual_dir}")
        return personas

    for path in sorted(individual_dir.glob("*.json")):
        try:
            base_payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(base_payload, dict):
                continue

            persona_id = base_payload.get("persona_id") or path.stem
            base_payload["persona_id"] = persona_id

            if traits_dir:
                traits_path = traits_dir / f"{persona_id}.json"
                if traits_path.exists():
                    traits_payload = json.loads(traits_path.read_text(encoding="utf-8"))
                    if isinstance(traits_payload, dict):
                        for key in (
                            "key_indicators",
                            "style_profile",
                            "value_frame",
                            "reasoning_policies",
                            "content_filters",
                        ):
                            if key in traits_payload:
                                base_payload[key] = traits_payload[key]

            personas.append(PersonaProfileModel(**base_payload))
        except Exception as exc:
            logger.warning(f"Failed to load persona profile {path}: {exc}")

    return personas


def build_registry(personas: List[PersonaProfileModel]) -> PersonaRegistry:
    registry = PersonaRegistry()
    for persona in personas:
        if persona.persona_id:
            registry.upsert(persona.persona_id, persona)
    return registry


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def build_fact_data_index(*, processed_dir: Path = PROCESSED_DATA_DIR) -> Optional[FactDataRAGIndex]:
    """Build the FactData RAG index at startup (optional)."""

    if not _env_flag("ADSP_FACTDATA_RAG_ENABLED", True):
        return None

    try:
        from adsp.data_pipeline.fact_data_pipeline.extract_raw.config import FactDataExtractionConfig
    except Exception as exc:  # pragma: no cover - optional dependency guard
        logger.debug(f"Fact data pipeline unavailable: {exc}")
        return None

    cfg = FactDataExtractionConfig()
    cfg.fact_data_output_dir = processed_dir / "fact_data"

    markdown_dir = Path(
        os.environ.get(
            "ADSP_FACTDATA_MARKDOWN_DIR",
            str(cfg.fact_data_output_dir / "pages"),
        )
    )
    markdown_pattern = os.environ.get("ADSP_FACTDATA_MARKDOWN_PATTERN", "page_*.md")

    index = build_fact_data_index_from_markdown(markdown_dir, pattern=markdown_pattern)
    if index is not None:
        logger.info(f"Fact data RAG ready ({len(index.indexed_chunk_ids)} chunks)")
        return index

    json_dir = Path(os.environ.get("ADSP_FACTDATA_JSON_DIR", str(cfg.raw_responses_dir)))
    if json_dir.exists() and any(json_dir.glob("page_*.json")):
        try:
            from adsp.data_pipeline.fact_data_pipeline.extract_raw import run_json_to_markdown_conversion

            converted = run_json_to_markdown_conversion(json_dir, markdown_dir)
            logger.info(f"Converted {converted} fact data JSON pages -> markdown for indexing")
        except Exception as exc:  # pragma: no cover - best effort conversion
            logger.warning(f"Fact data JSON->markdown conversion failed: {exc}")

        index = build_fact_data_index_from_markdown(markdown_dir, pattern=markdown_pattern)
        if index is not None:
            logger.info(f"Fact data RAG ready ({len(index.indexed_chunk_ids)} chunks)")
            return index

    if not _env_flag("ADSP_FACTDATA_RUN_EXTRACTION", False):
        return None

    if not cfg.vllm_model:
        logger.warning("Fact data extraction requested but no model configured; set `VLLM_MODEL`.")
        return None

    try:
        from adsp.data_pipeline.fact_data_pipeline.extract_raw import (
            run_fact_data_extraction_pipeline,
            run_json_to_markdown_conversion,
        )

        run_fact_data_extraction_pipeline(cfg)
        converted = run_json_to_markdown_conversion(cfg.raw_responses_dir, markdown_dir)
        logger.info(f"Converted {converted} extracted fact data pages -> markdown")
    except Exception as exc:  # pragma: no cover - external pipeline
        logger.warning(f"Fact data extraction pipeline failed: {exc}")
        return None

    index = build_fact_data_index_from_markdown(markdown_dir, pattern=markdown_pattern)
    if index is not None:
        logger.info(f"Fact data RAG ready ({len(index.indexed_chunk_ids)} chunks)")
    return index


def build_default_orchestrator(
    *,
    processed_dir: Path = PROCESSED_DATA_DIR,
) -> Orchestrator:
    """Create an orchestrator wired for local execution.

    - Loads persona profiles from `data/processed/personas/individual`
    - Loads reasoning traits from `data/processed/personas/common_traits` when present
    - Builds an in-memory RAG index over persona indicators
    """

    individual_dir, traits_dir = resolve_persona_paths(processed_dir)
    personas = load_personas_from_disk(individual_dir, traits_dir=traits_dir)

    registry = build_registry(personas)
    prompt_builder = PromptBuilder(registry=registry)

    persona_index = PersonaRAGIndex()
    persona_index.index_personas(personas)
    retriever = RAGPipeline(persona_index=persona_index)

    fact_data_index = build_fact_data_index(processed_dir=processed_dir)

    return Orchestrator(
        prompt_builder=prompt_builder,
        retriever=retriever,
        fact_data_index=fact_data_index,
    )


__all__ = [
    "resolve_persona_paths",
    "load_personas_from_disk",
    "build_registry",
    "build_fact_data_index",
    "build_default_orchestrator",
]
