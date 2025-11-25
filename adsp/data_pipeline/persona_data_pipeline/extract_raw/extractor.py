"""LLM-based page extractor using an OpenAI-compatible client."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, Sequence

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
        if not self.model:
            raise ValueError(
                "Set VLLM_MODEL to the OpenAI-compatible vision model name (e.g., llava)."
            )

    def extract_pages(
        self,
        pages: Sequence[PageImage],
        on_result: Optional[Callable[[PageExtractionResult], None]] = None,
    ) -> List[PageExtractionResult]:
        if not pages:
            return []
        results: List[PageExtractionResult] = []
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            future_map = {executor.submit(self._extract_single_page, page): page for page in pages}
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

    def _extract_single_page(self, page: PageImage) -> PageExtractionResult:
        encoded_image = encode_image_base64(page.image_path)
        content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encoded_image}"},
        }
        last_error: Optional[str] = None
        raw_text = ""
        for attempt in range(1, self.max_retries + 1):  # max_retries + initial try
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract persona patch for this page."},
                                content,
                            ],
                        },
                    ],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.response_timeout,
                )
                raw_text = response.choices[0].message.content or ""
                parsed = self._parse_raw_response(raw_text)
                if parsed is None:
                    raise ValueError("Model returned unparsable JSON.")
                persona_id = parsed.get("persona_id")
                patch = parsed.get("patch") or {}
                return PageExtractionResult(
                    page_number=page.page_number,
                    raw_text=raw_text,
                    parsed=parsed,
                    persona_id=persona_id,
                    patch=patch,
                    error=None,
                )
            except Exception as exc:  # pragma: no cover - external call
                last_error = str(exc)
                logger.warning(
                    (
                        f"Extraction failed for page {page.page_number} "
                        f"(attempt {attempt}/{self.max_retries}): {exc}"
                    )
                )
                if attempt > self.max_retries:
                    break
                time.sleep(self.backoff_seconds * attempt)

        return PageExtractionResult(
            page_number=page.page_number,
            raw_text=raw_text,
            parsed=None,
            persona_id=None,
            patch={},
            error=last_error,
        )

    @staticmethod
    def _parse_raw_response(raw_text: str) -> Optional[dict]:
        cleaned = strip_json_markdown(raw_text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
