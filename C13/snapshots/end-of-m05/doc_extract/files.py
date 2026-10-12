"""Open a document's pages as pictures: PDF pages are drawn (rendered), image files are read."""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def is_pdf(path: Path) -> bool:
    """Decide by the first bytes, not by the name: a photo saved as .pdf is still a photo."""
    with open(path, "rb") as f:
        return f.read(5) == b"%PDF-"


def page_count(path: Path) -> int:
    if is_pdf(path):
        doc = pdfium.PdfDocument(path)
        try:
            return len(doc)
        finally:
            doc.close()
    return 1


def page_image(path: Path, page: int = 1, dpi: int = 200) -> Image.Image:
    """Page `page` (1 = first) as an RGB picture. A PDF page is drawn at `dpi` dots per inch."""
    if is_pdf(path):
        doc = pdfium.PdfDocument(path)
        try:
            img = doc[page - 1].render(scale=dpi / 72).to_pil()
        finally:
            doc.close()
        return img.convert("RGB")
    with Image.open(path) as img:
        return img.convert("RGB")


def page_size_pt(path: Path, page: int = 1) -> tuple[float, float]:
    """The size of a PDF page in points (as shown, after any /Rotate)."""
    doc = pdfium.PdfDocument(path)
    try:
        return tuple(doc[page - 1].get_size())  # type: ignore[return-value]
    finally:
        doc.close()
