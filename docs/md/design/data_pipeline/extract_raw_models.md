# Data Pipeline: Page Models (`PageImage`, `PageExtractionResult`)

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/models.py`

## Purpose

Provides minimal typed containers for:
- rendered page images
- extraction results per page

## Models

### `PageImage`

Fields:
- `page_number: int` (1-based)
- `image_path: Path`
- `width: int`, `height: int`

### `PageExtractionResult`

Fields:
- `page_number: int`
- `raw_text: str` (raw model output)
- `parsed: dict | None` (best-effort parsed JSON payload)
- `error: str | None` (capture parsing/extraction failures)

