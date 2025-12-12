# Data Pipeline: `PDFRenderer`

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/renderer.py`

## Purpose

`PDFRenderer` converts a PDF into page images used as inputs to the vision extractor.

## Responsibilities

- Render PDF pages as PNG images to an output directory
- Reuse previously rendered images when possible (cache)
- Return typed `PageImage` metadata objects

## Public API

### `render(pdf_path: Path, output_dir: Path, page_range: (int,int) | None, reuse_existing_images: bool) -> list[PageImage]`

**Inputs**
- `pdf_path`: path to PDF
- `output_dir`: directory for rendered images (`page_XXXX.png`)
- `page_range`: optional inclusive 1-based page range
- `reuse_existing_images`: if `True`, reuse existing PNGs when readable

**Output**
- List of `PageImage` objects with:
  - `page_number`, `image_path`, `width`, `height`

## Rendering backends

1. **Primary**: PyMuPDF (`fitz`)
   - Efficient rendering via `page.get_pixmap(dpi=...)`
2. **Fallback**: `pdf2image`
   - Can render per page or entire doc

## Key dependencies / technologies

- `pymupdf` (`fitz`) OR `pdf2image`
- `Pillow` (`PIL.Image`) for reading existing images (cache reuse)
- `loguru` logging

## Failure modes

- Missing PDF → `FileNotFoundError` raised by the pipeline before render
- Missing render dependencies → `ImportError` with install guidance

