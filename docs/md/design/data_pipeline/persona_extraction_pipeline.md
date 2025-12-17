# Data Pipeline: `PersonaExtractionPipeline`

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/pipeline.py`

## Purpose

`PersonaExtractionPipeline` converts a PDF segmentation study into:
- structured page-level JSON outputs
- merged persona profiles (`personas.json` + per-persona files)
- optional reasoning enrichment artifacts (style/value/guardrails per persona)

This is the “PDF → structured persona JSON” backbone referenced in `docs/md/design.md` and `docs/md/persona_extraction_pipeline.md`.

## High-level stages

The pipeline is implemented as a LangChain `RunnableSequence`:

1. Render PDF pages to images (`PDFRenderer`)
2. Plan extraction, optionally reusing cached page responses
3. Extract structured JSON per page using a vision-capable model (`VLLMOpenAIExtractor`)
4. Merge page outputs into persona profiles (`PersonaMerger`)
5. (Optional) Reason over salient indicators to derive persona traits (`PersonaReasoner`)

## Public API

### `run() -> dict[str, Any]`

Returns the final state dict containing:
- `personas`: list of persona payloads
- `personas_map`: persona_id → payload dict
- `general_content`: extracted general content blocks
- `pages`: raw page payloads
- `page_results`: list of `PageExtractionResult`

### Helper: `run_persona_extraction_pipeline(config: PersonaExtractionConfig | None) -> dict`

Convenience wrapper to create and run the pipeline.

## Inputs

Configured via `PersonaExtractionConfig` (see `docs/md/design/data_pipeline/persona_extraction_config.md`), including:
- `pdf_path`
- optional `page_range`
- vLLM/OpenAI-compatible model endpoint + model name
- output paths for interim and processed artifacts

## Outputs (filesystem)

Defaults (see config) write to:
- **Interim**
  - rendered pages: `data/interim/persona_extraction/page_images/page_XXXX.png`
  - raw page outputs: `data/interim/persona_extraction/pages/page_XXXX.json`
  - QA report: `data/interim/persona_extraction/qa_report.json`
  - optional structured dump: `data/interim/persona_extraction/pages_structured.json`
- **Processed**
  - merged personas bundle: `data/processed/personas/personas.json`
  - per-persona profiles: `data/processed/personas/individual/{persona_id}.json`
  - reasoning traits: `data/processed/personas/common_traits/{persona_id}.json`

## Caching behavior

When `reuse_cache=True`:
- The pipeline loads existing `pages/page_XXXX.json` files and skips re-extraction for pages without errors.
- Reasoning enrichment also reuses existing `{persona_id}.json` trait outputs if present.

## Key dependencies / technologies

- `langchain_core.runnables` for pipeline composition (`RunnableLambda`, `RunnableSequence`)
- `loguru` logging
- Vision + reasoning model calls via the `openai` Python client configured with `base_url` to a vLLM/OpenAI-compatible server

