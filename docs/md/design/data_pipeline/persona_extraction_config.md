# Data Pipeline: `PersonaExtractionConfig`

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/config.py`

## Purpose

Central configuration object for the persona extraction pipeline, including:
- file paths for inputs/outputs
- model endpoints and decoding params
- caching / concurrency settings
- reasoning enrichment toggles

## Key configuration groups

### Input/output paths

Defaults are derived from `adsp/config.py` directory constants:
- `pdf_path` (default raw PDF under `data/raw/...`)
- `page_images_dir`, `raw_responses_dir` (interim outputs)
- `merged_output_path`, `persona_output_dir` (processed persona profiles)
- `reasoning_output_dir` (processed reasoning traits)
- `qa_report_path`, `structured_pages_output_path` (interim artifacts)

### Rendering

- `dpi`: resolution for page image render (default `300`)
- `page_range`: optional inclusive `(start, end)` 1-based
- `context_window`: number of adjacent pages to send as context for each extraction call

### Vision extraction (OpenAI-compatible)

Environment variables:
- `VLLM_BASE_URL` (default `http://localhost:8000/v1`)
- `VLLM_MODEL` (required)
- `VLLM_API_KEY` (default `EMPTY`)

Parameters:
- `temperature`, `top_p`
- `max_tokens`, `response_timeout`
- `max_concurrent_requests`, `max_retries`, `backoff_seconds`
- `max_image_bytes` (compress images to remain under payload limits)

### Reasoning enrichment (optional)

Toggle:
- `generate_reasoning_profiles` (default `True`)

Environment variables:
- `REASONING_BASE_URL` (defaults to `VLLM_BASE_URL`)
- `REASONING_MODEL` (optional; falls back to `VLLM_MODEL`)
- `REASONING_API_KEY` (defaults to `VLLM_API_KEY`)

Parameters:
- `reasoning_temperature`, `reasoning_top_p`
- `reasoning_max_tokens`
- `reasoning_max_input_chars` (chunking control)
- `reasoning_max_concurrent`

## Notes

- Use `scripts/run_persona_extraction.py` to override config values via CLI flags.
- For deterministic extraction, the defaults set `temperature=0.0` and very low `top_p`.

