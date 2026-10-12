"""Reading order: in which order a person reads the lines of a page.

    python -m doc_extract.layout D054          # the policy in two columns: naive order vs column order

A naive reader takes the lines top to bottom across the whole page. On a page with two columns,
that mixes the columns: half a sentence from the left, then half a sentence from the right.
reading_order() finds the gap between the columns and reads the left column first.
"""

from __future__ import annotations

import re
import sys

from doc_extract.pages import Line, Page


def naive_order(page: Page) -> list[Line]:
    """Top to bottom, then left to right, across the whole page."""
    return sorted(page.lines, key=lambda ln: (round(ln.box[1] / 3), ln.box[0]))


def find_gutter(lines: list[Line], width: float) -> float | None:
    """The x position of an empty vertical band between two columns, or None for one column."""
    if len(lines) < 6:
        return None
    best, best_width = None, 0.0
    lo, hi = int(width * 0.3), int(width * 0.7)
    x = lo
    while x < hi:
        start = x
        while x < hi and not any(ln.box[0] < x < ln.box[2] for ln in lines):
            x += 1
        if x - start > best_width:
            best, best_width = (start + x) / 2, x - start
        x += 1
    if best is None or best_width < 8:
        return None
    left = sum(1 for ln in lines if ln.box[2] < best)
    right = sum(1 for ln in lines if ln.box[0] > best)
    return best if left >= 3 and right >= 3 else None


def reading_order(page: Page) -> list[Line]:
    """Lines in reading order: full-width lines split the page into bands; in each band, the left
    column, then the right column."""
    body = [ln for ln in page.lines]
    spans = [ln for ln in body if not _narrow(ln, page.width)]
    narrow = [ln for ln in body if _narrow(ln, page.width)]
    gutter = find_gutter(narrow, page.width)
    if gutter is None:
        return naive_order(page)
    crossing = [ln for ln in body if ln.box[0] < gutter < ln.box[2] or ln in spans]
    wide = sorted(crossing, key=lambda ln: ln.box[1])
    cols = [ln for ln in body if all(ln is not w for w in wide)]
    out: list[Line] = []
    edges = [float("-inf")] + [ln.box[1] for ln in wide] + [float("inf")]
    for i in range(len(edges) - 1):
        band = [ln for ln in cols if edges[i] <= ln.box[1] < edges[i + 1]]
        for side in (lambda ln: ln.box[2] <= gutter, lambda ln: ln.box[0] >= gutter):
            out += sorted((ln for ln in band if side(ln)), key=lambda ln: (ln.box[1], ln.box[0]))
        if i < len(wide):
            out.append(wide[i])
    return out


def _narrow(ln: Line, width: float) -> bool:
    return (ln.box[2] - ln.box[0]) < width * 0.6


def text_of(lines: list[Line]) -> str:
    return " ".join(ln.text for ln in lines)


def kept_whole(text: str, paragraphs: list[str]) -> int:
    """How many paragraphs appear in the text unbroken, word for word."""
    t = re.sub(r"\s+", " ", text)
    return sum(1 for p in paragraphs if re.sub(r"\s+", " ", p) in t)


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents, textlayer

    argv = sys.argv[1:] if argv is None else argv
    d = documents.get(argv[0] if argv else "D054")
    paragraphs = [s["text"] for s in d.truth.get("sections", []) if s["kind"] in ("p", "li")]
    naive_all, ordered_all = [], []
    for page in textlayer.read(d.path):
        naive_all += naive_order(page)
        ordered_all += reading_order(page)
        g = find_gutter([ln for ln in page.lines if _narrow(ln, page.width)], page.width)
        print(f"{d.file}, page {page.page}: " + (f"two columns, gap at x = {g:.0f} pt" if g else "one column"))
    print("\nFirst 12 lines, naive order (top to bottom across the page):")
    for ln in naive_all[:12]:
        print(f"  {ln.text}")
    print("\nFirst 12 lines, reading order (column by column):")
    for ln in ordered_all[:12]:
        print(f"  {ln.text}")
    if paragraphs:
        n = len(paragraphs)
        print(f"\nParagraphs kept whole: naive {kept_whole(text_of(naive_all), paragraphs)} of {n}, "
              f"reading order {kept_whole(text_of(ordered_all), paragraphs)} of {n}")


if __name__ == "__main__":
    main()
