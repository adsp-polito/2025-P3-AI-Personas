"""Helpers to build a runnable local system configuration."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from typing import List, Optional, Tuple

from loguru import logger

from adsp.config import PROCESSED_DATA_DIR
from adsp.core.orchestrator import Orchestrator
from adsp.core.persona_registry import PersonaRegistry
from adsp.core.prompt_builder import PromptBuilder
from adsp.core.rag import RAGPipeline
from adsp.core.rag.fact_data_index import FactDataRAGIndex, build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import PersonaRAGIndex
from adsp.data_pipeline.embedding_utils import (
    build_configured_embeddings,
    get_configured_embedding_config,
    get_configured_embedding_model_name,
    get_configured_embedding_signature,
)
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import PersonaIndicatorRAG
from adsp.data_pipeline.schema import PersonaProfileModel
from adsp.storage.langchain_vectorstore import VectorStoreProvider, get_vectorstore_config
from adsp.utils.progress import progress_bar


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


def _fingerprint_paths(paths: List[Path], *, label: str) -> str:
    digest = hashlib.sha256()
    digest.update(label.encode("utf-8"))
    digest.update(get_configured_embedding_signature().encode("utf-8"))

    for path in sorted({Path(p) for p in paths}, key=lambda item: str(item)):
        digest.update(str(path).encode("utf-8"))
        if not path.exists():
            digest.update(b"missing")
            continue
        stat = path.stat()
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))

    return digest.hexdigest()


def _collect_persona_source_paths(individual_dir: Path, traits_dir: Optional[Path]) -> List[Path]:
    paths = list(individual_dir.glob("*.json")) if individual_dir.exists() else []
    if traits_dir and traits_dir.exists():
        paths.extend(traits_dir.glob("*.json"))
    return sorted(paths, key=lambda path: str(path))


def _collect_factdata_source_paths(markdown_dir: Path, *, pattern: str) -> List[Path]:
    if not markdown_dir.exists():
        return []
    return sorted((path for path in markdown_dir.rglob(pattern) if path.is_file()), key=lambda path: str(path))


def _factdata_fingerprint(markdown_dir: Path, *, pattern: str) -> str | None:
    fact_paths = _collect_factdata_source_paths(markdown_dir, pattern=pattern)
    if not fact_paths:
        return None
    return _fingerprint_paths(fact_paths, label=f"fact-data:{pattern}")


def _log_runtime_rag_config() -> None:
    embedding_config = get_configured_embedding_config()
    vectorstore_config = get_vectorstore_config()
    logger.info(
        "QA runtime config: embedding_backend={} embedding_model={} device={} batch_size={} api_base_url={}",
        embedding_config.backend,
        embedding_config.model_name,
        embedding_config.device or "n/a",
        embedding_config.batch_size or "default",
        embedding_config.api_base_url or "n/a",
    )
    logger.info(
        "QA runtime config: vectorstore_backend={} persist_dir={} reset_on_startup={}",
        vectorstore_config.backend,
        vectorstore_config.persist_dir,
        vectorstore_config.reset_on_startup,
    )


def build_fact_data_index(
    *,
    processed_dir: Path = PROCESSED_DATA_DIR,
    embeddings=None,
    vectorstore_provider: Optional[VectorStoreProvider] = None,
) -> Optional[FactDataRAGIndex]:
    """Build the FactData RAG index at startup (optional)."""

    if not _env_flag("ADSP_FACTDATA_RAG_ENABLED", True):
        logger.info("QA bootstrap step 5/6: fact-data RAG disabled by env")
        return None

    try:
        from adsp.data_pipeline.fact_data_pipeline.extract_raw.config import (
            FactDataExtractionConfig,
        )
    except Exception as exc:  # pragma: no cover - optional dependency guard
        logger.debug(f"Fact data pipeline unavailable: {exc}")
        return None

    start_total = time.perf_counter()
    cfg = FactDataExtractionConfig()
    cfg.fact_data_output_dir = processed_dir / "fact_data"

    markdown_dir = Path(
        os.environ.get(
            "ADSP_FACTDATA_MARKDOWN_DIR",
            str(cfg.fact_data_output_dir),
        )
    )
    markdown_pattern = os.environ.get("ADSP_FACTDATA_MARKDOWN_PATTERN", "*.md")
    logger.info(
        "QA bootstrap step 5/6: preparing fact-data RAG from {} (pattern={})",
        markdown_dir,
        markdown_pattern,
    )

    resolved_embeddings = embeddings or build_configured_embeddings()
    fact_fingerprint = _factdata_fingerprint(markdown_dir, pattern=markdown_pattern)

    index = build_fact_data_index_from_markdown(
        markdown_dir,
        embeddings=resolved_embeddings,
        vectorstore_provider=vectorstore_provider,
        fingerprint=fact_fingerprint,
        pattern=markdown_pattern,
    )
    if index is not None:
        if index.loaded_from_persisted:
            logger.info(
                "QA bootstrap step 5/6: loaded persisted fact-data vector store in {:.2f}s",
                time.perf_counter() - start_total,
            )
        else:
            logger.info(
                "QA bootstrap step 5/6: fact-data RAG ready ({} chunks) in {:.2f}s",
                len(index.indexed_chunk_ids),
                time.perf_counter() - start_total,
            )
        return index

    if markdown_dir.exists() and any(markdown_dir.rglob(markdown_pattern)):
        index = build_fact_data_index_from_markdown(
            markdown_dir,
            embeddings=resolved_embeddings,
            vectorstore_provider=vectorstore_provider,
            fingerprint=fact_fingerprint,
            pattern=markdown_pattern,
        )
        if index is not None:
            if index.loaded_from_persisted:
                logger.info(
                    "QA bootstrap step 5/6: loaded persisted fact-data vector store in {:.2f}s",
                    time.perf_counter() - start_total,
                )
            else:
                logger.info(
                    "QA bootstrap step 5/6: fact-data RAG ready ({} chunks) in {:.2f}s",
                    len(index.indexed_chunk_ids),
                    time.perf_counter() - start_total,
                )
            return index

    if not _env_flag("ADSP_FACTDATA_RUN_EXTRACTION", False):
        logger.info("QA bootstrap step 5/6: no fact-data markdown found; extraction disabled")
        return None

    if not cfg.vllm_model:
        logger.warning("Fact data extraction requested but no model configured; set `VLLM_MODEL`.")
        return None

    try:
        from adsp.data_pipeline.fact_data_pipeline.extract_raw import (
            run_fact_data_extraction_pipeline,
        )

        logger.info("QA bootstrap step 5/6: running fact-data extraction during startup")
        run_fact_data_extraction_pipeline(cfg)
        logger.info("Fact data extraction completed - markdown files generated")
        fact_fingerprint = _factdata_fingerprint(markdown_dir, pattern=markdown_pattern)
    except Exception as exc:  # pragma: no cover - external pipeline
        logger.warning(f"Fact data extraction pipeline failed: {exc}")
        return None

    index = build_fact_data_index_from_markdown(
        markdown_dir,
        embeddings=resolved_embeddings,
        vectorstore_provider=vectorstore_provider,
        fingerprint=fact_fingerprint,
        pattern=markdown_pattern,
    )
    if index is not None:
        if index.loaded_from_persisted:
            logger.info(
                "QA bootstrap step 5/6: loaded persisted fact-data vector store in {:.2f}s",
                time.perf_counter() - start_total,
            )
        else:
            logger.info(
                "QA bootstrap step 5/6: fact-data RAG ready ({} chunks) in {:.2f}s",
                len(index.indexed_chunk_ids),
                time.perf_counter() - start_total,
            )
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

    start_total = time.perf_counter()

    logger.info("QA bootstrap step 1/6: resolving persona directories")
    individual_dir, traits_dir = resolve_persona_paths(processed_dir)
    logger.info(
        "QA bootstrap step 1/6: individual_dir={} traits_dir={}",
        individual_dir,
        traits_dir,
    )

    start_step = time.perf_counter()
    logger.info("QA bootstrap step 2/6: loading persona profiles from disk")
    personas = load_personas_from_disk(individual_dir, traits_dir=traits_dir)
    logger.info(
        "QA bootstrap step 2/6: loaded {} personas in {:.2f}s",
        len(personas),
        time.perf_counter() - start_step,
    )

    start_step = time.perf_counter()
    logger.info("QA bootstrap step 3/6: building persona registry")
    registry = build_registry(personas)
    logger.info(
        "QA bootstrap step 3/6: registry ready with {} personas in {:.2f}s",
        len(registry.list_personas()),
        time.perf_counter() - start_step,
    )

    logger.info("QA bootstrap step 4/6: building prompt builder and persona RAG")
    prompt_builder = PromptBuilder(registry=registry)
    _log_runtime_rag_config()
    embeddings = build_configured_embeddings()
    logger.info("QA bootstrap step 4/6: embedding model initialized once and shared")
    vectorstore_provider = VectorStoreProvider(embeddings=embeddings)
    logger.info("QA bootstrap step 4/6: vector store provider initialized once and shared")
    start_step = time.perf_counter()
    persona_index = PersonaRAGIndex(
        embeddings=embeddings,
        vectorstore_provider=vectorstore_provider,
    )
    persona_sources = _collect_persona_source_paths(individual_dir, traits_dir)
    persona_fingerprint = _fingerprint_paths(persona_sources, label="persona")
    loaded_persona_stores = 0
    rebuilt_persona_stores = 0
    total_personas = len(personas)
    with progress_bar(
        total=total_personas,
        desc="Indexing personas",
        unit="persona",
        leave=False,
    ) as progress:
        for persona in personas:
            if not persona.persona_id:
                progress.update(1)
                progress.set_postfix(status="skipped", persona_id="missing")
                continue
            namespace = f"persona-{persona.persona_id}"
            store = vectorstore_provider.load(namespace, fingerprint=persona_fingerprint)
            if store is not None:
                persona_index.attach_persona_vectorstore(
                    persona.persona_id,
                    vectorstore=store,
                    namespace=namespace,
                )
                loaded_persona_stores += 1
                progress.update(1)
                progress.set_postfix(status="loaded", persona_id=persona.persona_id)
                continue

            store = vectorstore_provider.create(namespace, reset=True)
            rag = PersonaIndicatorRAG(
                embeddings,
                vectorstore=store,
                namespace=namespace,
            )
            rag.index_persona(persona)
            vectorstore_provider.persist(
                namespace,
                fingerprint=persona_fingerprint,
                vectorstore=store,
            )
            persona_index.attach_persona_vectorstore(
                persona.persona_id,
                vectorstore=store,
                namespace=namespace,
            )
            rebuilt_persona_stores += 1
            progress.update(1)
            progress.set_postfix(status="rebuilt", persona_id=persona.persona_id)
    retriever = RAGPipeline(persona_index=persona_index)
    logger.info(
        "QA bootstrap step 4/6: persona RAG ready for {} personas in {:.2f}s (loaded={}, rebuilt={})",
        len(personas),
        time.perf_counter() - start_step,
        loaded_persona_stores,
        rebuilt_persona_stores,
    )

    fact_data_index = build_fact_data_index(
        processed_dir=processed_dir,
        embeddings=embeddings,
        vectorstore_provider=vectorstore_provider,
    )

    logger.info("QA bootstrap step 6/6: assembling orchestrator")
    orchestrator = Orchestrator(
        prompt_builder=prompt_builder,
        retriever=retriever,
        fact_data_index=fact_data_index,
    )
    logger.info(
        "QA bootstrap complete in {:.2f}s",
        time.perf_counter() - start_total,
    )
    return orchestrator


__all__ = [
    "resolve_persona_paths",
    "load_personas_from_disk",
    "build_registry",
    "build_fact_data_index",
    "build_default_orchestrator",
]
