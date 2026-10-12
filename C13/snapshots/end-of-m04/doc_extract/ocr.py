"""Path 2: OCR on the CPU with RapidOCR (ONNX Runtime), with the box and score of every line.

    python -m doc_extract.ocr D021            # OCR every page, print the lines
    python -m doc_extract.ocr D021 --prepare  # prepare the image first (prepare.py)

Results are kept in out/cache/ocr/, so the second run of the same page is instant.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from functools import lru_cache
from pathlib import Path

from PIL import Image

from doc_extract import files
from doc_extract.pages import Line, Page

OCR_DPI = int(os.environ.get("OCR_DPI", "200"))  # PDF pages are drawn at this resolution before OCR
# The text finder works on a copy at most this many pixels long. RapidOCR's default is 2000; at
# 1280 a batch of the course's pages peaks at about 1.4 GB instead of about 2.2 GB, with the same
# fields right (reference measurement: runs/memory.json).
MAX_SIDE = int(os.environ.get("OCR_MAX_SIDE", "1280"))
CACHE = Path("out/cache/ocr")


@lru_cache(maxsize=2)
def engine(turn_lines: bool = False):
    """The OCR engine. turn_lines=True also runs RapidOCR's line classifier, which turns lines that
    look upside down; this project turns whole pages in prepare.py instead."""
    from rapidocr import RapidOCR

    params = {"Global.log_level": "error", "Global.use_cls": turn_lines, "Global.max_side_len": MAX_SIDE}
    threads = int(os.environ.get("OCR_THREADS", "0"))
    if threads > 0:  # fewer threads: a little slower, less memory
        params["EngineConfig.onnxruntime.intra_op_num_threads"] = threads
    return RapidOCR(params=params)


def engine_name() -> str:
    from importlib.metadata import version

    return f"rapidocr {version('rapidocr')}"


def lines_from_image(img: Image.Image) -> tuple[list[Line], float]:
    """OCR one picture. Returns the lines and the seconds it took."""
    t = time.perf_counter()
    result = engine()(img.convert("RGB"))
    seconds = time.perf_counter() - t
    out = []
    if result.boxes is not None:
        for poly, text, score in zip(result.boxes, result.txts, result.scores):
            xs, ys = [float(p[0]) for p in poly], [float(p[1]) for p in poly]
            (ax, ay), (bx, by) = poly[0], poly[1]
            angle = math.degrees(math.atan2(float(by - ay), float(bx - ax)))
            out.append(Line(str(text), (min(xs), min(ys), max(xs), max(ys)), round(float(score), 4),
                            round(max(ys) - min(ys), 1), False, round(angle, 2)))
    return out, seconds


def _key(path: Path, page: int, prepare: bool) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return f"{h}-p{page}-{OCR_DPI}-{MAX_SIDE}-{'prep' if prepare else 'raw'}-{engine_name().replace(' ', '-')}"


def read(path: Path, pages: list[int] | None = None, prepare: bool = False, cache: bool = True) -> list[Page]:
    """OCR every page (or the pages listed). Boxes are in pixels of the picture that was read:
    for an image file, the original image; for a PDF, the page drawn at OCR_DPI."""
    out = []
    for p in range(1, files.page_count(path) + 1):
        if pages and p not in pages:
            continue
        key = CACHE / f"{_key(path, p, prepare)}.json"
        if cache and key.exists():
            out.append(Page.from_dict(json.loads(key.read_text(encoding="utf-8"))))
            continue
        t0 = time.perf_counter()  # the time of the whole page: drawing it, preparing it, reading it
        img = files.page_image(path, p, OCR_DPI)
        steps: dict = {}
        if prepare:
            from doc_extract import prepare as prep

            img, steps = prep.prepare(img)
        lines, _ = lines_from_image(img)
        seconds = time.perf_counter() - t0
        dpi = OCR_DPI if files.is_pdf(path) else 0
        page = Page(path.name, p, img.width, img.height, "px", "ocr", lines, round(seconds, 3), engine_name(), dpi, steps)
        if prepare:
            from doc_extract import prepare as prep

            page = prep.to_original(page)
        if cache:
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_text(json.dumps(page.to_dict(), ensure_ascii=False), encoding="utf-8")
        out.append(page)
    return out


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents

    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("usage: python -m doc_extract.ocr DOC_ID [--prepare]")
    d = documents.get(argv[0])
    for page in read(d.path, prepare="--prepare" in argv):
        low = sum(1 for ln in page.lines if ln.score < 0.8)
        print(f"{d.file}, page {page.page}: {len(page.lines)} lines by {page.engine} in {page.seconds:.2f} s "
              f"({low} with a score under 0.80)")
        for ln in page.lines[:60]:
            x0, top, x1, bottom = ln.box
            print(f"  {ln.score:.2f} [{x0:6.0f} {top:6.0f} {x1:6.0f} {bottom:6.0f}]  {ln.text}")


if __name__ == "__main__":
    main()
