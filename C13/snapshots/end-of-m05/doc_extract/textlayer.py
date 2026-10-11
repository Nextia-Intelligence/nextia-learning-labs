"""Path 1: read the text layer of a digital PDF, with the box of every line (pdfplumber).

    python -m doc_extract.textlayer D001
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pdfplumber

from doc_extract.pages import Line, Page

ENGINE = f"pdfplumber {pdfplumber.__version__}"


def lines_from_words(words: list[dict], gap: float = 1.5) -> list[Line]:
    """Join words into lines: same row, and closer than `gap` x the font size to the next word.

    A wide space (a column gap, or the space between a label and its amount on a receipt)
    starts a new line, as an OCR engine also does."""
    out: list[Line] = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        size = float(w.get("size", w["bottom"] - w["top"]))
        bold = "Bold" in str(w.get("fontname", ""))
        if out:
            last = out[-1]
            same_row = abs(w["top"] - last.box[1]) < 0.4 * size
            near = 0 <= w["x0"] - last.box[2] < gap * size
            if same_row and near:
                last.text += " " + w["text"].replace("(cid:127)", "•")
                last.box = (last.box[0], min(last.box[1], w["top"]), w["x1"], max(last.box[3], w["bottom"]))
                last.bold = last.bold and bold
                continue
        out.append(Line(w["text"].replace("(cid:127)", "•"), (w["x0"], w["top"], w["x1"], w["bottom"]), 1.0, round(size, 1), bold))
    return out


def read(path: Path, pages: list[int] | None = None) -> list[Page]:
    """Every page's lines from the text layer. A scanned page gives a page with no lines."""
    out = []
    with pdfplumber.open(path) as pdf:
        for i, p in enumerate(pdf.pages, 1):
            if pages and i not in pages:
                continue
            t = time.perf_counter()
            words = p.extract_words(extra_attrs=["size", "fontname"], x_tolerance=1.5, y_tolerance=2)
            lines = lines_from_words(words)
            out.append(Page(path.name, i, float(p.width), float(p.height), "pt", "text", lines,
                            round(time.perf_counter() - t, 4), ENGINE))
    return out


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents

    argv = sys.argv[1:] if argv is None else argv
    d = documents.get(argv[0] if argv else "D001")
    for page in read(d.path):
        print(f"{d.file}, page {page.page}: {len(page.lines)} lines from the text layer "
              f"({page.width:.0f} x {page.height:.0f} pt)")
        for ln in page.lines[:40]:
            x0, top, x1, bottom = ln.box
            print(f"  [{x0:6.1f} {top:6.1f} {x1:6.1f} {bottom:6.1f}]  {ln.text}")
        if not page.lines:
            print("  (no text layer: this page is a picture. Use OCR.)")


if __name__ == "__main__":
    main()
