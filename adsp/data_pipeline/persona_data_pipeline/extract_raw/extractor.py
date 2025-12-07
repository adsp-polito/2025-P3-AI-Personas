"""LLM-based page extractor using an OpenAI-compatible client."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, List, Optional, Sequence

from loguru import logger

from .config import PersonaExtractionConfig
from .models import PageExtractionResult, PageImage
from .prompts import SYSTEM_PROMPT
from .utils import encode_image_base64, strip_json_markdown


class VLLMOpenAIExtractor:
    def __init__(self, config: PersonaExtractionConfig):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "openai client is required for persona extraction. "
                "Install with `pip install openai`."
            ) from exc

        self.client = OpenAI(base_url=config.vllm_base_url, api_key=config.vllm_api_key)
        self.model = config.vllm_model
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.max_tokens = config.max_tokens
        self.response_timeout = config.response_timeout
        self.max_retries = config.max_retries
        self.backoff_seconds = config.backoff_seconds
        self.max_concurrent = max(1, config.max_concurrent_requests)
        self.context_window = max(0, getattr(config, "context_window", 0))
        self.max_image_bytes = getattr(config, "max_image_bytes", None)
        if not self.model:
            raise ValueError(
                "Set VLLM_MODEL to the OpenAI-compatible vision model name (e.g., llava)."
            )

    def extract_pages(
        self,
        pages: Sequence[PageImage],
        on_result: Optional[Callable[[PageExtractionResult], None]] = None,
        all_pages: Optional[Sequence[PageImage]] = None,
        context_window: Optional[int] = None,
    ) -> List[PageExtractionResult]:
        if not pages:
            return []
        all_pages = all_pages or pages
        window = self.context_window if context_window is None else max(0, context_window)
        page_lookup = {p.page_number: p for p in all_pages}
        results: List[PageExtractionResult] = []
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            future_map = {
                executor.submit(
                    self._extract_single_page,
                    page,
                    self._build_context_pages(page, page_lookup, window),
                ): page
                for page in pages
            }
            for future in as_completed(future_map):
                result = future.result()
                results.append(result)
                if on_result:
                    try:
                        on_result(result)
                    except Exception as exc:  # pragma: no cover - defensive logging
                        logger.warning(
                            f"Failed to handle on_result for page {result.page_number}: {exc}"
                        )
        return sorted(results, key=lambda r: r.page_number)

    def _extract_single_page(
        self, page: PageImage, context_pages: Sequence[PageImage]
    ) -> PageExtractionResult:
        last_error: Optional[str] = None
        raw_text = ""
        total_attempts = max(1, self.max_retries + 1)
        for attempt in range(1, total_attempts + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": self._build_user_content(page, context_pages),
                        },
                    ],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.response_timeout,
                )
                raw_text = response.choices[0].message.content or ""
                parsed = self._select_parsed_for_page(
                    self._parse_raw_response(raw_text), page.page_number
                )
                if parsed is None:
                    raise ValueError("Model returned unparsable JSON.")
                return PageExtractionResult(
                    page_number=page.page_number,
                    raw_text=raw_text,
                    parsed=parsed,
                    error=None,
                )
            except Exception as exc:  # pragma: no cover - external call
                last_error = str(exc)
                logger.warning(
                    (
                        f"Extraction failed for page {page.page_number} "
                        f"(attempt {attempt}/{total_attempts}): {exc}"
                    )
                )
                if attempt >= total_attempts:
                    break
                time.sleep(self.backoff_seconds * attempt)

        return PageExtractionResult(
            page_number=page.page_number,
            raw_text=raw_text,
            parsed=None,
            error=last_error,
        )

    @staticmethod
    def _parse_raw_response(raw_text: str) -> Optional[Any]:
        cleaned = strip_json_markdown(raw_text)
        candidates = [cleaned]

        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidates.append(cleaned[start : end + 1])
        if "[" in cleaned and "]" in cleaned:
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end != -1 and end > start:
                candidates.append(cleaned[start : end + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _build_context_pages(
        page: PageImage, page_lookup: dict[int, PageImage], window: int
    ) -> List[PageImage]:
        if window <= 0:
            return [page]
        neighbors = [page.page_number]
        for offset in range(1, window + 1):
            for candidate in (page.page_number - offset, page.page_number + offset):
                if candidate in page_lookup:
                    neighbors.append(candidate)
        ordered = [page.page_number] + sorted(
            {num for num in neighbors if num != page.page_number}
        )
        return [page_lookup[num] for num in ordered]

    def _image_content(self, page: PageImage) -> dict:
        encoded_image, mime_type = encode_image_base64(
            page.image_path,
            max_bytes=self.max_image_bytes,
        )
        mime = mime_type or "image/png"
        return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded_image}"}}

    def _build_user_content(
        self, primary_page: PageImage, context_pages: Sequence[PageImage]
    ) -> List[dict]:
        preface = (
            "Extract structured JSON for the primary slide below. "
            f"The primary slide number is {primary_page.page_number}. "
            "Use the other slides only as context to understand cross-page continuity "
            "and fill adjacent context/linking notes. Return JSON for the primary slide only."
        )
        content: List[dict] = [{"type": "text", "text": preface}]
        for ctx_page in context_pages:
            label = "Primary slide" if ctx_page.page_number == primary_page.page_number else "Context slide"
            content.append({"type": "text", "text": f"{label} #{ctx_page.page_number}"})
            content.append(self._image_content(ctx_page))
        return content

    @staticmethod
    def _select_parsed_for_page(parsed: Any, page_number: int) -> Optional[dict]:
        if parsed is None:
            return None
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                metadata = item.get("page_metadata") or {}
                number = metadata.get("page_number")
                try:
                    normalized = int(number)
                except Exception:
                    normalized = number
                if normalized == page_number:
                    return item
            for item in parsed:
                if isinstance(item, dict):
                    return item
        return None
