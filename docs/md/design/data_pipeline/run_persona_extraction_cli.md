# Data Pipeline: Running Persona Extraction (CLI)

**Code**: `scripts/run_persona_extraction.py`

## Purpose

Provides a CLI wrapper around `PersonaExtractionPipeline` so engineers can run extraction locally and control config values without editing code.

## Basic usage

```bash
python scripts/run_persona_extraction.py --vllm-model <vision-model-name>
```

## Required environment / dependencies

- Python deps installed (`openai`, `pymupdf` or `pdf2image`, `Pillow`, `loguru`, `langchain-core`)
- An OpenAI-compatible server for the vision model (commonly vLLM), configured via:
  - `--vllm-base-url` / `VLLM_BASE_URL`
  - `--vllm-model` / `VLLM_MODEL`

Optional reasoning enrichment requires a text model:
- `--reasoning-model` / `REASONING_MODEL` (or reuse the vision model if it supports text)

## What it writes

See `docs/md/design/data_pipeline/persona_extraction_pipeline.md` for the default output locations (interim + processed).

## Common flags (high value)

- `--pdf-path`: input PDF
- `--page-range start,end`: limit run to a subset of pages
- `--no-cache`: re-run extraction even if cached page outputs exist
- `--concurrency`: parallel extraction calls
- `--disable-reasoning-profiles`: skip enrichment step

