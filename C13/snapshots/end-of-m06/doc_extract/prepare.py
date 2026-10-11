"""Prepare a picture before OCR: turn it upright, straighten it, crop it to the document, enlarge
small text. The original file is never changed: every step is written down, so a box found on
the prepared picture can be drawn back on the original (to_original).

    python -m doc_extract.prepare D027      # writes out/prepared/D027-p1.png and prints the steps
"""

from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from doc_extract.pages import Line, Page

TARGET_TEXT_PX = 32  # OCR reads best when a line of text is about this many pixels high
MAX_SCALE = 2.5


def _rotation_matrix(size: tuple[int, int], angle: float, expand: bool) -> tuple[list[float], tuple[int, int]]:
    """The matrix that Pillow's Image.rotate(angle, expand) uses: it maps a point of the rotated
    picture to the point of the original picture. Returns it and the rotated picture's size."""
    w, h = size
    a = -math.radians(angle % 360.0)
    m = [round(math.cos(a), 15), round(math.sin(a), 15), 0.0, round(-math.sin(a), 15), round(math.cos(a), 15), 0.0]

    def tr(x, y):
        return m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5]

    cx, cy = w / 2.0, h / 2.0
    m[2], m[5] = tr(-cx, -cy)
    m[2] += cx
    m[5] += cy
    nw, nh = w, h
    if expand:
        xx, yy = [], []
        for x, y in ((0, 0), (w, 0), (w, h), (0, h)):
            x, y = tr(x, y)
            xx.append(x)
            yy.append(y)
        nw = math.ceil(max(xx)) - math.floor(min(xx))
        nh = math.ceil(max(yy)) - math.floor(min(yy))
        m[2], m[5] = tr(-(nw - w) / 2.0, -(nh - h) / 2.0)
    return m, (nw, nh)


def _apply(m: list[float], x: float, y: float) -> tuple[float, float]:
    return m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5]


def content_box(img: Image.Image, pad: int = 16) -> tuple[int, int, int, int]:
    """The box around the document on the picture: the bright paper on a darker table, or the
    printed part of a white scanner page."""
    g = np.asarray(img.convert("L").resize((img.width // 4 or 1, img.height // 4 or 1)), dtype=np.float32)
    background = float(np.median(np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]])))
    if background > 200:  # a white page: keep what is printed on it
        mask = g < background - 60
    else:  # a photo: keep the paper, brighter than the table
        mask = g > background + 35
    rows_hit = np.nonzero(mask.sum(axis=1) >= 2)[0]
    cols_hit = np.nonzero(mask.sum(axis=0) >= 2)[0]
    if len(rows_hit) < 5 or len(cols_hit) < 5:
        return (0, 0, img.width, img.height)
    x0, x1, y0, y1 = cols_hit[0], cols_hit[-1] + 1, rows_hit[0], rows_hit[-1] + 1
    return (max(0, int(x0) * 4 - pad), max(0, int(y0) * 4 - pad),
            min(img.width, int(x1) * 4 + pad), min(img.height, int(y1) * 4 + pad))


def _quick_read(img: Image.Image) -> tuple[float, int, float, float]:
    """OCR a small copy: (mean score x share of wide boxes, characters, median slope, median text height)."""
    from doc_extract import ocr

    small = img.copy()
    small.thumbnail((1000, 1000))
    lines, _ = ocr.lines_from_image(small)
    if not lines:
        return 0.0, 0, 0.0, 0.0
    wide = sum(1 for ln in lines if ln.box[2] - ln.box[0] > ln.height) / len(lines)
    chars = sum(len(ln.text) for ln in lines)
    score = statistics.fmean(ln.score for ln in lines) * wide
    long_angles = [ln.angle for ln in lines if ln.box[2] - ln.box[0] > 3 * ln.height] or [0.0]
    heights = [ln.height * img.width / small.width for ln in lines]
    return score, chars, statistics.median(long_angles), statistics.median(heights)


def prepare(img: Image.Image) -> tuple[Image.Image, dict]:
    """Crop, turn upright, straighten and enlarge. Returns the new picture and the steps."""
    steps: dict = {"original_size": [img.width, img.height]}
    box = content_box(img)
    if box != (0, 0, img.width, img.height):
        img = img.crop(box)
        steps["crop"] = list(box)
    # Upright: try the page as it is; only if it reads badly, try the three other quarter turns.
    best = (_quick_read(img), 0)
    if best[0][0] < 0.85:
        for turn in (90, 180, 270):
            r = _quick_read(img.rotate(turn, expand=True))
            if r[0] * max(r[1], 1) > best[0][0] * max(best[0][1], 1) * 1.15:
                best = (r, turn)
    (_, _, slope, text_px), turn = best
    if turn:
        img = img.rotate(turn, expand=True)
        steps["turn"] = turn
    if abs(slope) > 1.0:
        img = img.rotate(slope, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
        steps["deskew"] = round(slope, 2)
    if 0 < text_px < TARGET_TEXT_PX * 0.75:
        s = min(MAX_SCALE, TARGET_TEXT_PX / text_px)
        img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
        steps["scale"] = round(s, 3)
    return img, steps


def point_to_original(x: float, y: float, steps: dict) -> tuple[float, float]:
    """A point on the prepared picture -> the same point on the original picture."""
    w, h = steps["original_size"]
    sizes = []
    if "crop" in steps:
        c = steps["crop"]
        w, h = c[2] - c[0], c[3] - c[1]
    sizes.append((w, h))
    mats = []
    if "turn" in steps:
        m, (w, h) = _rotation_matrix((w, h), steps["turn"], True)
        mats.append(m)
    if "deskew" in steps:
        m, (w, h) = _rotation_matrix((w, h), steps["deskew"], True)
        mats.append(m)
    if "scale" in steps:
        x, y = x / steps["scale"], y / steps["scale"]
    for m in reversed(mats):
        x, y = _apply(m, x, y)
    if "crop" in steps:
        x, y = x + steps["crop"][0], y + steps["crop"][1]
    return x, y


def to_original(page: Page) -> Page:
    """Move every box of a page read from a prepared picture back onto the original picture."""
    steps = page.prepared
    if not steps or set(steps) == {"original_size"}:
        return page
    lines = []
    for ln in page.lines:
        x0, y0, x1, y1 = ln.box
        pts = [point_to_original(x, y, steps) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        a = ln.angle + steps.get("deskew", 0) + steps.get("turn", 0)  # the slope on the original picture
        lines.append(Line(ln.text, (min(xs), min(ys), max(xs), max(ys)), ln.score, ln.size, ln.bold, round(a, 2)))
    w, h = steps["original_size"]
    return Page(page.file, page.page, w, h, page.unit, page.path, lines, page.seconds, page.engine, page.dpi, steps)


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents, files

    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("usage: python -m doc_extract.prepare DOC_ID")
    d = documents.get(argv[0])
    out = Path("out/prepared")
    out.mkdir(parents=True, exist_ok=True)
    for p in range(1, files.page_count(d.path) + 1):
        from doc_extract import ocr

        img = files.page_image(d.path, p, ocr.OCR_DPI)
        new, steps = prepare(img)
        target = out / f"{d.doc_id}-p{p}.png"
        new.save(target)
        done = ", ".join(f"{k} {v}" for k, v in steps.items() if k != "original_size") or "nothing to do"
        print(f"{d.file}, page {p}: {img.width} x {img.height} -> {new.width} x {new.height}: {done}")
        print(f"  prepared picture: {target} (the original file is not changed)")


if __name__ == "__main__":
    main()
