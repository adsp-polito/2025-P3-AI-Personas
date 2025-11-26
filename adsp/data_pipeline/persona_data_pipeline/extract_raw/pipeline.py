"""Persona extraction pipeline orchestrator."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional, Sequence

from loguru import logger

from .config import PersonaExtractionConfig
from .extractor import VLLMOpenAIExtractor
from .merger import PersonaMerger
from .models import PageExtractionResult, PageImage
from .renderer import PDFRenderer


class PersonaExtractionPipeline:
    def __init__(self, config: Optional[PersonaExtractionConfig] = None):
        self.config = config or PersonaExtractionConfig()
        self.renderer = PDFRenderer(dpi=self.config.dpi)
        self.extractor = VLLMOpenAIExtractor(self.config)
        self.merger = PersonaMerger(
            document_name=self.config.pdf_path.name,
            merge_strategy=self.config.merge_strategy,
        )

    def run(self) -> Dict[str, Any]:
        if not self.config.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {self.config.pdf_path}")
        logger.info("Starting persona extraction pipeline")
        pages = self.renderer.render(
            self.config.pdf_path,
            self.config.page_images_dir,
            self.config.page_range,
            reuse_existing_images=self.config.reuse_cache,
        )
        logger.info(f"Rendered {len(pages)} pages from {self.config.pdf_path}")

        cached_results: Dict[int, PageExtractionResult] = {}
        if self.config.reuse_cache:
            cached_results = self._load_cached_results(pages)
            if cached_results:
                logger.info(
                    f"Reusing cached responses for {len(cached_results)} pages from "
                    f"{self.config.raw_responses_dir}"
                )
        else:
            logger.info("Cache reuse disabled; all pages will be extracted.")

        pages_to_extract = [page for page in pages if page.page_number not in cached_results]
        if pages_to_extract:
            logger.info(
                f"Extracting personas for {len(pages_to_extract)} pages "
                f"(max_concurrent_requests={self.extractor.max_concurrent})"
            )
            new_results = self.extractor.extract_pages(
                pages_to_extract, on_result=lambda r: self._persist_page_results([r])
            )
        else:
            logger.info("No remaining pages to extract after applying cache.")
            new_results = []

        page_results = sorted(
            [*cached_results.values(), *new_results], key=lambda r: r.page_number
        )
        logger.info(f"Merging and writing outputs for {len(page_results)} pages processed")
        for result in page_results:
            self.merger.apply_page_result(result)

        self.merger.write_outputs(
            self.config.merged_output_path, self.config.qa_report_path, page_results
        )
        return {"personas": self.merger.personas, "page_results": page_results}

    def _load_cached_results(self, pages: Sequence[PageImage]) -> Dict[int, PageExtractionResult]:
        cached: Dict[int, PageExtractionResult] = {}
        for page in pages:
            cache_path = self.config.raw_responses_dir / f"page_{page.page_number:04d}.json"
            if not cache_path.exists():
                continue
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                parsed = payload.get("parsed") if isinstance(payload, dict) else None
                if parsed is not None and not isinstance(parsed, dict):
                    parsed = None
                patch = payload.get("patch") if isinstance(payload, dict) else {}
                if not isinstance(patch, dict):
                    patch = {}
                if not patch and parsed:
                    patch = parsed.get("patch") or {}
                    if not isinstance(patch, dict):
                        patch = {}
                persona_id = None
                if isinstance(payload, dict):
                    persona_id = payload.get("persona_id")
                if persona_id is None and parsed:
                    persona_id = parsed.get("persona_id")
                raw_text = payload.get("raw_text", "") if isinstance(payload, dict) else ""
                error = payload.get("error") if isinstance(payload, dict) else None
                if error:
                    logger.info(
                        f"Skipping cached page {page.page_number} because previous run failed: {error}"
                    )
                    continue
                cached[page.page_number] = PageExtractionResult(
                    page_number=page.page_number,
                    raw_text=raw_text,
                    parsed=parsed,
                    persona_id=persona_id,
                    patch=patch,
                    error=error,
                )
            except Exception as exc:
                logger.warning(
                    f"Could not load cached result for page {page.page_number} ({cache_path}): {exc}"
                )
        return cached

    def _persist_page_results(self, results: Iterable[PageExtractionResult]) -> None:
        self.config.raw_responses_dir.mkdir(parents=True, exist_ok=True)
        if self.config.debug:
            self.config.debug_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            out_path = self.config.raw_responses_dir / f"page_{result.page_number:04d}.json"
            payload = {
                "page": result.page_number,
                "persona_id": result.persona_id,
                "parsed": result.parsed,
                "error": result.error,
                "raw_text": result.raw_text,
                "patch": result.patch,
            }
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.debug(f"Wrote raw response for page {result.page_number} -> {out_path}")
            if self.config.debug:
                debug_path = self.config.debug_dir / f"page_{result.page_number:04d}.txt"
                debug_payload = result.raw_text or ""
                with debug_path.open("w", encoding="utf-8") as f:
                    f.write(debug_payload)
                logger.debug(f"Wrote debug raw text for page {result.page_number} -> {debug_path}")


def run_persona_extraction_pipeline(
    config: Optional[PersonaExtractionConfig] = None,
) -> Dict[str, Any]:
    pipeline = PersonaExtractionPipeline(config)
    return pipeline.run()
