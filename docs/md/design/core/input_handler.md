# Core: `InputHandler`

**Code**: `adsp/core/input_handler/__init__.py`

## Purpose

`InputHandler` normalizes user inputs before retrieval and prompt building.

## Responsibilities

- Normalize text input (current)
- (Planned) route and preprocess multimodal inputs:
  - PDF text extraction + page selection
  - Image preprocessing and OCR / captioning

## Public API

### `normalize(text: str) -> str`

**Input**
- raw text string

**Output**
- stripped text string (`text.strip()`)

## Key dependencies / technologies

- Python `dataclasses`

## Notes / production hardening

To meet `docs/md/design.md` multimodal requirements, expand this component with:
- PDF extraction via `pymupdf` (`fitz`) or `pdf2image` + OCR
- Attachment routing into the pipeline used in `adsp/data_pipeline/persona_data_pipeline/extract_raw/`

