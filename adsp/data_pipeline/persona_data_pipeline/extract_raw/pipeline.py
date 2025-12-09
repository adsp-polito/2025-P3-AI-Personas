"""Persona extraction pipeline orchestrator."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence

from langchain_core.runnables import RunnableLambda, RunnableSequence, RunnableSerializable
from loguru import logger

from .config import PersonaExtractionConfig
from .extractor import VLLMOpenAIExtractor
from .merger import PersonaMerger
from .models import PageExtractionResult, PageImage
from .renderer import PDFRenderer
from .reasoner import PersonaReasoner


class PersonaExtractionPipeline:
    def __init__(self, config: Optional[PersonaExtractionConfig] = None):
        self.config = config or PersonaExtractionConfig()
        self.renderer = PDFRenderer(dpi=self.config.dpi)
        self.extractor = VLLMOpenAIExtractor(self.config)
        self.merger = PersonaMerger(
            document_name=self.config.pdf_path.name,
            merge_strategy=self.config.merge_strategy,
        )
        self.reasoner = PersonaReasoner(self.config)
        self._chain: RunnableSequence = self._build_chain()

    def _build_chain(self) -> RunnableSerializable[Any, Any]:
        """
        This is the core of the orchestration. It uses LangChain's Runnable protocol to define the pipeline as a chain of
        functions. The | (pipe) operator passes the output of one step as the input to the next. The steps are:
        1. _render_pages: Render PDF to images
        2. _prepare_extraction_plan: Check cache and determine which pages to extract
        3. _extract_and_collect: Call the VLLM for the necessary pages
        4. _merge_and_write: Merge all results and write them to disk
        5. _run_reasoner: Run the final reasoning step to enrich the profiles
        """
        return (
            RunnableLambda(self._render_pages).with_config(run_name="RenderPages")
            | RunnableLambda(self._prepare_extraction_plan).with_config(run_name="PrepareExtractionPlan")
            | RunnableLambda(self._extract_and_collect).with_config(run_name="ExtractPages")
            | RunnableLambda(self._merge_and_write).with_config(run_name="MergeOutputs")
            | RunnableLambda(self._run_reasoner).with_config(run_name="Reasoner")
        )

    def run(self) -> Dict[str, Any]:
        return self._chain.invoke({}, config={"run_name": "PersonaExtractionPipeline"})

    def _render_pages(self, _: Dict[str, Any]) -> Dict[str, Any]:
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

        return {"pages": pages}

    def _prepare_extraction_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pages: Sequence[PageImage] = state["pages"]
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
        return {**state, "cached_results": cached_results, "pages_to_extract": pages_to_extract}

    def _extract_and_collect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pages_to_extract: Sequence[PageImage] = state["pages_to_extract"]
        cached_results: Dict[int, PageExtractionResult] = state["cached_results"]
        new_results: List[PageExtractionResult]
        if pages_to_extract:
            logger.info(
                f"Extracting personas for {len(pages_to_extract)} pages "
                f"(max_concurrent_requests={self.extractor.max_concurrent})"
            )
            new_results = self.extractor.extract_pages(
                pages_to_extract,
                all_pages=state["pages"],
                context_window=self.config.context_window,
                on_result=lambda r: self._persist_page_results([r]),
            )
        else:
            logger.info("No remaining pages to extract after applying cache.")
            new_results = []

        page_results = sorted(
            [*cached_results.values(), *new_results], key=lambda r: r.page_number
        )
        return {**state, "page_results": page_results}

    def _merge_and_write(self, state: Dict[str, Any]) -> Dict[str, Any]:
        page_results: Sequence[PageExtractionResult] = state["page_results"]
        logger.info(f"Merging and writing outputs for {len(page_results)} pages processed")
        for result in page_results:
            self.merger.apply_page_result(result)

        self.merger.write_outputs(
            self.config.merged_output_path,
            self.config.qa_report_path,
            page_results,
            persona_output_dir=self.config.persona_output_dir,
        )
        self._write_page_outputs(page_results)
        return {
            "personas": list(self.merger.personas.values()),
            "personas_map": self.merger.personas,
            "general_content": self.merger.general_content,
            "pages": self.merger.pages,
            "page_results": page_results,
        }

    def _run_reasoner(self, state: Dict[str, Any]) -> Dict[str, Any]:
        persona_map = state.get("personas_map") or self.merger.personas
        self.reasoner.process(
            persona_map,
            output_dir=self.config.reasoning_output_dir,
            reuse_cache=self.config.reuse_cache,
        )
        return state

    def _write_page_outputs(self, page_results: Sequence[PageExtractionResult]) -> None:
        path = self.config.structured_pages_output_path
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "page": r.page_number,
                "parsed": r.parsed,
                "error": r.error,
                "raw_text": r.raw_text,
            }
            for r in page_results
        ]
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote structured page outputs to {path}")

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
                "parsed": result.parsed,
                "error": result.error,
                "raw_text": result.raw_text,
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
