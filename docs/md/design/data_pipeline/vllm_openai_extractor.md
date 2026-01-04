# Data Pipeline: `VLLMOpenAIExtractor`

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/extractor.py`

## Purpose

Extracts structured JSON from page images using a vision-capable model exposed via an OpenAI-compatible API (commonly vLLM).

## Responsibilities

- Build a multimodal request payload (text + image(s))
- Call `chat.completions.create(...)` against an OpenAI-compatible server
- Parse model output into JSON (with guardrails for markdown fences and malformed output)
- Run page extraction concurrently (thread pool)
- Retry with backoff on failures

## Public API

### `extract_pages(pages: Sequence[PageImage], *, all_pages: Sequence[PageImage] | None, context_window: int | None, on_result: Callable | None) -> list[PageExtractionResult]`

**Inputs**
- `pages`: list of primary pages to extract
- `all_pages`: used to look up adjacent pages for context windows
- `context_window`: number of neighboring pages to include on each side
- `on_result`: optional callback invoked after each page completes (used to persist intermediates)

**Output**
- Sorted list of `PageExtractionResult { page_number, raw_text, parsed, error }`

## Request construction

Messages:
- `system`: `SYSTEM_PROMPT` (see `docs/md/design/data_pipeline/prompts.md`)
- `user`: list of content blocks:
  - text preface indicating the primary page number
  - one or more image blocks in OpenAI “image_url” format with `data:{mime};base64,...`

Images are base64-encoded and optionally compressed via `encode_image_base64()` to stay under payload limits.

## Parsing strategy

1. Strip markdown fences (`strip_json_markdown`)
2. Try parsing:
   - full cleaned content
   - best-effort substring `{...}` and `[...]`
3. If output is a list, select the item matching the requested page number (fallback to first dict)

## Key dependencies / technologies

- `openai` Python client (configured with `base_url` for OpenAI-compatible servers)
- `concurrent.futures.ThreadPoolExecutor`
- `loguru` logging

## Failure modes

- `VLLM_MODEL` missing → `ValueError` on initialization
- Non-JSON output → `PageExtractionResult.error` contains message; page is skipped during caching reuse
- Server/API errors → retried up to `max_retries` with `backoff_seconds * attempt`

