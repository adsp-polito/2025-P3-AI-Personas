# Data Pipeline: `PersonaMerger`

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/merger.py`

## Purpose

`PersonaMerger` aggregates page-level extraction results into:
- a merged persona bundle (`personas.json`)
- per-persona profile files (`individual/{persona_id}.json`)
- QA report for validation and parse failures

## Responsibilities

- Consume `PageExtractionResult` objects and merge their `parsed` payloads
- Resolve and stabilize `persona_id` values (slugify)
- Stamp indicator sources with doc_id + page references for traceability
- Merge repeated indicators/fields across pages
- Emit QA report (missing persona_name, parse failures, etc.)

## Key behaviors

### Persona ID resolution

For each `persona_data` dict on a page:
- Prefer `persona_id`, else `persona_name`, else fallback `persona-page-{page_number}-{n}`
- Normalize via `_slugify()` (lowercase + kebab-case)

### Source stamping

`_stamp_indicator_sources()` ensures every indicator has:
- `sources[].doc_id` set (defaults to `document_name`)
- `sources[].pages` includes the current page number

### Deep merge strategy

`_deep_merge(target, incoming, parent_path)` merges dicts/lists/scalars with simple rules:
- Scalars default to “fill” (only write if missing) unless `merge_strategy[path]="overwrite"`
- Lists default to append + deduplicate (unless overwritten)
- `indicators` lists receive special merge logic to merge by indicator key (`id` / `indicator_id` / `label`)

The `merge_strategy` dict is a dotted-path override (e.g., `"summary_bio": "overwrite"`).

## Public API

### `apply_page_result(result: PageExtractionResult) -> None`

Applies a single page result into the internal aggregate state:
- `personas` map
- `general_content`
- `pages`
- `parse_failures`

### `write_outputs(output_path: Path, qa_report_path: Path, page_results: Sequence[PageExtractionResult], persona_output_dir: Path | None) -> None`

Writes:
- merged payload to `output_path`
- individual persona JSON files to `persona_output_dir` (if provided)
- QA report to `qa_report_path`

## Key dependencies / technologies

- `json` for output writing
- `loguru` logging

