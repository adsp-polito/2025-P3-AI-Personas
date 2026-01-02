"""Fact data extraction pipeline orchestrator."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence

from langchain_core.runnables import RunnableLambda, RunnableSequence, RunnableSerializable
from loguru import logger

from .config import FactDataExtractionConfig
from .extractor import VLLMOpenAIExtractor
from .models import PageExtractionResult, PageImage
from .renderer import PDFRenderer


class FactDataExtractionPipeline:
    def __init__(self, config: Optional[FactDataExtractionConfig] = None):
        self.config = config or FactDataExtractionConfig()
        
        self.renderer = PDFRenderer(dpi=self.config.dpi)
        self.extractor = VLLMOpenAIExtractor(self.config)
        self._chain: RunnableSequence = self._build_chain()

    def _build_chain(self) -> RunnableSerializable[Any, Any]:
        """
        This is the core of the orchestration. It uses LangChain's Runnable protocol to define the pipeline as a chain of
        functions. The | (pipe) operator passes the output of one step as the input to the next. The steps are:
        1. _render_pages: Render PDF to images
        2. _prepare_extraction_plan: Check cache and determine which pages to extract
        3. _extract_and_collect: Call the VLLM for the necessary pages
        4. _write_page: Write result to disk
        """
        return (
            RunnableLambda(self._render_pages).with_config(run_name="RenderPages")
            | RunnableLambda(self._prepare_extraction_plan).with_config(run_name="PrepareExtractionPlan")
            | RunnableLambda(self._extract_and_collect).with_config(run_name="ExtractPages")
            | RunnableLambda(self._write_page).with_config(run_name="WritePageOutputs")
        )

    def run(self) -> Dict[str, Any]:
        return self._chain.invoke({}, config={"run_name": "FactDataExtractionPipeline"})

    def _render_pages(self, _: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {self.config.pdf_path}")
        logger.info("Starting fact data extraction pipeline")
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
                f"Extracting fact data for {len(pages_to_extract)} pages "
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

    def _write_page(self, state: Dict[str, Any]) -> Dict[str, Any]:
        page_results: Sequence[PageExtractionResult] = state["page_results"]
        logger.info(f"Writing markdown outputs for {len(page_results)} pages processed")
        
        self._write_markdown_files(page_results)

        # return the final state, which contains the page-level results
        return state

    def _write_markdown_files(self, page_results: Sequence[PageExtractionResult]) -> None:
        """Write extracted markdown content directly to data/processed/fact_data/pages directory."""
        output_dir = self.config.fact_data_output_dir / "pages"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for result in page_results:
            if result.error:
                logger.warning(f"Skipping page {result.page_number} due to error: {result.error}")
                continue
            
            output_path = output_dir / f"page_{result.page_number:04d}.md"
            with output_path.open("w", encoding="utf-8") as f:
                f.write(result.markdown_content)
            logger.debug(f"Wrote markdown for page {result.page_number} -> {output_path}")
        
        logger.info(f"Wrote {len([r for r in page_results if not r.error])} markdown files to {output_dir}")

    def _load_cached_results(self, pages: Sequence[PageImage]) -> Dict[int, PageExtractionResult]:
        cached: Dict[int, PageExtractionResult] = {}
        for page in pages:
            # Check markdown cache first
            markdown_cache_path = self.config.fact_data_output_dir / "pages" / f"page_{page.page_number:04d}.md"
            if markdown_cache_path.exists():
                try:
                    with markdown_cache_path.open("r", encoding="utf-8") as f:
                        markdown_content = f.read()
                    cached[page.page_number] = PageExtractionResult(
                        page_number=page.page_number,
                        markdown_content=markdown_content,
                        error=None,
                    )
                    continue
                except Exception as exc:
                    logger.warning(
                        f"Could not load cached markdown for page {page.page_number} ({markdown_cache_path}): {exc}"
                    )
            
            # Fall back to old JSON cache format if it exists
            cache_path = self.config.raw_responses_dir / f"page_{page.page_number:04d}.json"
            if not cache_path.exists():
                continue
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                markdown_content = payload.get("markdown_content", "") if isinstance(payload, dict) else ""
                error = payload.get("error") if isinstance(payload, dict) else None
                if error:
                    logger.info(
                        f"Skipping cached page {page.page_number} because previous run failed: {error}"
                    )
                    continue
                if markdown_content:
                    cached[page.page_number] = PageExtractionResult(
                        page_number=page.page_number,
                        markdown_content=markdown_content,
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
                "markdown_content": result.markdown_content,
                "error": result.error,
            }
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.debug(f"Wrote raw response for page {result.page_number} -> {out_path}")
            if self.config.debug:
                debug_path = self.config.debug_dir / f"page_{result.page_number:04d}.md"
                debug_payload = result.markdown_content or ""
                with debug_path.open("w", encoding="utf-8") as f:
                    f.write(debug_payload)
                logger.debug(f"Wrote debug markdown for page {result.page_number} -> {debug_path}")


def run_fact_data_extraction_pipeline(
        config: Optional[FactDataExtractionConfig] = None,
) -> Dict[str, Any]:
    pipeline = FactDataExtractionPipeline(config)
    return pipeline.run()
