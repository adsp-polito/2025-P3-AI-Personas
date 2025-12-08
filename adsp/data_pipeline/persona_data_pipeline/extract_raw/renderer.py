"""PDF rendering utilities. Convert PDF pages into images"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from loguru import logger

from .models import PageImage


class PDFRenderer:
    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def render(
        self,
        pdf_path: Path,
        output_dir: Path,
        page_range: Optional[tuple[int, int]] = None,
        reuse_existing_images: bool = True,
    ) -> List[PageImage]:
        """
        It tries to use the PyMuPDF library (fitz) first because it's generally faster. If PyMuPDF
        is not installed, it falls back to using pdf2image
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            import fitz  # type: ignore

            return self._render_with_pymupdf(pdf_path, output_dir, page_range, reuse_existing_images)
        except ImportError:
            try:
                return self._render_with_pdf2image(
                    pdf_path, output_dir, page_range, reuse_existing_images
                )
            except ImportError as exc:
                raise ImportError(
                    "Install `pymupdf` or `pdf2image` to render PDF pages. "
                    "Example: pip install pymupdf pdf2image"
                ) from exc
        except Exception as exc:  # pragma: no cover - rendering fallback
            logger.error(f"Failed to render PDF with PyMuPDF: {exc}")
            raise

    @staticmethod
    def _load_existing_image(image_path: Path, page_number: int) -> Optional[PageImage]:
        if not image_path.exists():
            return None
        try:
            from PIL import Image  # type: ignore
        except ImportError:
            logger.debug("Pillow not installed; cannot reuse existing page image.")
            return None
        try:
            with Image.open(image_path) as img:
                width, height = img.size
            return PageImage(
                page_number=page_number,
                image_path=image_path,
                width=width,
                height=height,
            )
        except Exception as exc:
            logger.warning(f"Failed to read existing page image {image_path}: {exc}")
            return None

    def _render_with_pymupdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        page_range: Optional[tuple[int, int]],
        reuse_existing_images: bool,
    ) -> List[PageImage]:
        import fitz  # type: ignore

        doc = fitz.open(pdf_path)
        start, end = page_range if page_range else (1, doc.page_count)
        images: List[PageImage] = []

        for page_idx in range(start - 1, end):
            out_path = output_dir / f"page_{page_idx + 1:04d}.png"
            if reuse_existing_images:
                existing = self._load_existing_image(out_path, page_idx + 1)
                if existing:
                    images.append(existing)
                    logger.debug(f"Reusing rendered page {page_idx + 1} -> {out_path}")
                    continue
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(dpi=self.dpi)
            pix.save(out_path)
            images.append(
                PageImage(
                    page_number=page_idx + 1,
                    image_path=out_path,
                    width=pix.width,
                    height=pix.height,
                )
            )
            logger.debug(f"Rendered page {page_idx + 1} -> {out_path}")
        return images

    def _render_with_pdf2image(
        self,
        pdf_path: Path,
        output_dir: Path,
        page_range: Optional[tuple[int, int]],
        reuse_existing_images: bool,
    ) -> List[PageImage]:
        from pdf2image import convert_from_path, pdfinfo_from_path  # type: ignore

        start: int
        end: Optional[int]
        if page_range:
            start, end = page_range
        else:
            try:
                info = pdfinfo_from_path(pdf_path)
                end = int(info.get("Pages", 0))
                if end <= 0:
                    raise ValueError("Page count not available")
                start = 1
            except Exception as exc:  # pragma: no cover - best-effort fallback
                logger.warning(f"Could not read PDF info to reuse renders: {exc}")
                start, end = 1, None

        page_images: List[PageImage] = []
        missing_pages: List[int] = []

        if end is not None:
            for idx in range(start, end + 1):
                out_path = output_dir / f"page_{idx:04d}.png"
                if reuse_existing_images:
                    existing = self._load_existing_image(out_path, idx)
                    if existing:
                        page_images.append(existing)
                        logger.debug(f"Reusing rendered page {idx} -> {out_path}")
                        continue
                missing_pages.append(idx)

            if not missing_pages:
                return sorted(page_images, key=lambda p: p.page_number)

            for page_number in missing_pages:
                images = convert_from_path(
                    pdf_path,
                    dpi=self.dpi,
                    first_page=page_number,
                    last_page=page_number,
                )
                for image in images:
                    out_path = output_dir / f"page_{page_number:04d}.png"
                    image.save(out_path, "PNG")
                    page_images.append(
                        PageImage(
                            page_number=page_number,
                            image_path=out_path,
                            width=image.width,
                            height=image.height,
                        )
                    )
                    logger.debug(f"Rendered page {page_number} -> {out_path}")
            return sorted(page_images, key=lambda p: p.page_number)

        images = convert_from_path(pdf_path, dpi=self.dpi)
        for idx, image in enumerate(images, start=start):
            out_path = output_dir / f"page_{idx:04d}.png"
            if reuse_existing_images:
                existing = self._load_existing_image(out_path, idx)
                if existing:
                    page_images.append(existing)
                    logger.debug(f"Reusing rendered page {idx} -> {out_path}")
                    continue
            image.save(out_path, "PNG")
            page_images.append(
                PageImage(
                    page_number=idx,
                    image_path=out_path,
                    width=image.width,
                    height=image.height,
                )
            )
            logger.debug(f"Rendered page {idx} -> {out_path}")
        return page_images
