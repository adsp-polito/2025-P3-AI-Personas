# Data Pipeline: Extraction Utilities

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/utils.py`

## Purpose

Helper functions used by the extraction pipeline to improve model interoperability and robustness.

## `strip_json_markdown(text: str) -> str`

**Goal**
- Models frequently return JSON wrapped in markdown fences (```json ... ```). This helper extracts the JSON body.

**Behavior**
- If no fences: returns stripped text
- If fences present:
  - splits on ``` blocks
  - prefers a block starting with `{` or `[` (or the largest block)

## `encode_image_base64(image_path: Path, max_bytes: int | None) -> (str, str)`

**Goal**
- Encode images as base64 for OpenAI “image_url” content.
- Compress to stay under request payload limits.

**Behavior**
- If raw PNG bytes <= `max_bytes`, return base64 PNG
- Else:
  - try converting to JPEG at decreasing quality
  - if still too large, downscale gradually and re-encode
  - fallback to raw PNG on any errors

**Output**
- `(base64_string, mime_type)` where mime is `"image/png"` or `"image/jpeg"`

**Dependencies**
- Uses `Pillow` when compression is needed
- Logs decisions via `loguru`

