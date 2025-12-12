# Running Persona Extraction (PDF → Personas)

The persona extraction pipeline renders PDF pages, calls a vision model to extract structured JSON, merges into persona profiles, and optionally runs a reasoning model to derive traits.

## Prerequisites

- Python environment with dependencies from `requirements.txt`
- A running OpenAI-compatible model server (commonly vLLM) that supports image inputs

## Configure model endpoint

You can provide config via CLI flags or environment variables:

- `VLLM_BASE_URL` (default `http://localhost:8000/v1`)
- `VLLM_MODEL` (required)
- `VLLM_API_KEY` (default `EMPTY`)

Optional reasoning model:
- `REASONING_BASE_URL` (defaults to `VLLM_BASE_URL`)
- `REASONING_MODEL` (optional; defaults to `VLLM_MODEL`)
- `REASONING_API_KEY` (defaults to `VLLM_API_KEY`)

## Run

```bash
python scripts/run_persona_extraction.py \
  --pdf-path "data/raw/lavazza/customer-segmentation/2023 03_FR_Consumers Segmentation France.pdf" \
  --vllm-model "<your-vision-model>" \
  --page-range 1,10
```

## Outputs

Default outputs are documented in:
- `docs/md/design/data_pipeline/persona_extraction_pipeline.md`

## Debugging tips

- Use `--no-cache` to force re-extraction of pages (ignores cached `pages/page_XXXX.json`).
- Use `--debug` to write raw model text to `data/interim/persona_extraction/debug/`.
- If model output is not parseable JSON, inspect `pages/page_XXXX.json` (`raw_text` and `error`).

