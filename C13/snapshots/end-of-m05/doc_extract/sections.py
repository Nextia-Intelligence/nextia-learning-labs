"""Sections and hierarchy: turn a policy's pages into titled blocks with their section path.

    python -m doc_extract.sections D054          # the returns policy: outline, footnotes, page furniture
    python -m doc_extract.sections D058 --parts  # where one document ends and the next begins

What it does, on the text layer:
  1. drops the page furniture: the running header and footer that repeat on every page;
  2. reads each page in reading order (layout.py), so two columns are not mixed;
  3. finds headings by their size and weight, and keeps the path of headings above each block
     (Returns policy > Return window);
  4. joins lines into paragraphs and list items;
  5. finds footnotes (small text at the bottom of a page) and links each one to its mark.
"""

from __future__ import annotations

import re
import statistics
import sys
from dataclasses import dataclass, field

from doc_extract import layout, textlayer
from doc_extract.pages import Line, Page

MARKS = "¹²³⁴⁵⁶⁷⁸⁹*"


@dataclass
class Block:
    kind: str  # title | heading | paragraph | list_item | footnote
    text: str
    path: list[str]
    page: int
    box: tuple[float, float, float, float]
    notes: list[str] = field(default_factory=list)  # footnotes linked to this block


def _union(lines: list[Line]) -> tuple[float, float, float, float]:
    return (min(ln.box[0] for ln in lines), min(ln.box[1] for ln in lines),
            max(ln.box[2] for ln in lines), max(ln.box[3] for ln in lines))


def furniture(pages: list[Page], band: float = 0.08) -> set[tuple[int, int]]:
    """(page, line index) of the running header and footer: lines near the top or bottom edge whose
    text, without numbers, repeats on most pages; and "Page 3"-style lines."""
    seen: dict[str, int] = {}
    edge: list[tuple[int, int, str]] = []
    for p in pages:
        for i, ln in enumerate(p.lines):
            if ln.box[1] < p.height * band or ln.box[3] > p.height * (1 - band):
                key = re.sub(r"\d+", "#", ln.text.strip().lower())
                edge.append((p.page, i, key))
                seen[key] = seen.get(key, 0) + 1
    need = max(2, (len(pages) + 1) // 2)
    return {(pg, i) for pg, i, key in edge if seen[key] >= need or re.fullmatch(r"page #( of #)?", key)}


def _flush(blocks: list[Block], cur: list[Line], kind: str, path: list[str], page: int) -> tuple[list[Line], str]:
    """End the current paragraph or list item: add it as a block. Returns an empty one."""
    if cur:
        text = re.sub(r"(\w)- (\w)", r"\1-\2", " ".join(ln.text for ln in cur))
        blocks.append(Block(kind, text.lstrip("• ").strip(), list(path), page, _union(cur)))
    return [], ""


def parse(pages: list[Page]) -> tuple[list[Block], list[str]]:
    """Blocks in reading order, and the page furniture that was dropped."""
    drop = furniture(pages)
    dropped = sorted({ln.text for p in pages for i, ln in enumerate(p.lines) if (p.page, i) in drop})
    sizes = [ln.size for p in pages for ln in p.lines if ln.size]
    body = statistics.median(sizes) if sizes else 10.0
    blocks: list[Block] = []
    path: list[str] = []
    for p in pages:
        keep = [ln for i, ln in enumerate(p.lines) if (p.page, i) not in drop]
        ordered = layout.reading_order(Page(p.file, p.page, p.width, p.height, p.unit, p.path, keep))
        notes_zone = p.height * 0.80
        cur: list[Line] = []
        kind = ""

        prev: Line | None = None
        for ln in ordered:
            small = ln.size and ln.size < body - 1.5
            if small and ln.box[1] > notes_zone and ln.text[:1] in MARKS:
                cur, kind = _flush(blocks, cur, kind, path, p.page)
                blocks.append(Block("footnote", ln.text, list(path), p.page, ln.box))
                prev = None
                continue
            if ln.size > body + 5:
                cur, kind = _flush(blocks, cur, kind, path, p.page)
                path = [ln.text]
                blocks.append(Block("title", ln.text, list(path), p.page, ln.box))
                prev = None
                continue
            if ln.size > body + 1 and ln.bold:
                cur, kind = _flush(blocks, cur, kind, path, p.page)
                path = path[:1] + [ln.text]
                blocks.append(Block("heading", ln.text, list(path), p.page, ln.box))
                prev = None
                continue
            new_item = ln.text.startswith("•")
            gap = (ln.box[1] - prev.box[3]) if prev else 0
            column_jump = prev is not None and (ln.box[1] < prev.box[1] or abs(ln.box[0] - prev.box[0]) > p.width * 0.3)
            if new_item or not cur or gap > ln.height * 0.45 or column_jump:
                if cur and kind == "list_item" and not new_item and not column_jump and gap <= ln.height * 0.45:
                    pass
                else:
                    cur, kind = _flush(blocks, cur, kind, path, p.page)
                    kind = "list_item" if new_item else "paragraph"
            cur.append(ln)
            prev = ln
        cur, kind = _flush(blocks, cur, kind, path, p.page)
    # Link each footnote to the block that holds its mark.
    for note in (b for b in blocks if b.kind == "footnote"):
        mark = note.text[0]
        for b in blocks:
            if b.kind != "footnote" and mark in b.text:
                b.notes.append(note.text)
                note.path = b.path
                break
    return blocks, dropped


def parts(pages_routes: list[tuple[int, str, str]]) -> list[tuple[int, int, str]]:
    """Where one document inside a file ends and the next begins: a new part starts when the way
    to read the page changes (text layer / picture) or a page starts with a new title.
    pages_routes: (page, route, first line). Returns (first page, last page, what it looks like)."""
    out: list[list] = []
    for page, route, first in pages_routes:
        if out and out[-1][2] == route and not first.isupper():
            out[-1][1] = page
        else:
            out.append([page, page, route])
    return [tuple(x) for x in out]


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents, route

    argv = sys.argv[1:] if argv is None else argv
    d = documents.get(argv[0] if argv else "D054")
    if "--parts" in argv:
        info = route.inspect(d.path)
        tl = {p.page: p for p in textlayer.read(d.path)}
        rows = [(p.page, p.route, (tl[p.page].lines[0].text if tl.get(p.page) and tl[p.page].lines else "")) for p in info.pages]
        for first, last, r in parts(rows):
            what = "text layer (a digital form or letter)" if r == "text" else "picture (a scan: read it with OCR)"
            print(f"{d.file}: pages {first}-{last}: {what}")
        return
    pages = textlayer.read(d.path)
    blocks, dropped = parse(pages)
    print(f"{d.file}: {len(pages)} pages, {len(blocks)} blocks")
    print(f"page furniture dropped: {dropped}")
    for b in blocks:
        if b.kind in ("title", "heading"):
            print(f"  p{b.page} {'#' * (1 if b.kind == 'title' else 2)} {b.text}")
        elif b.kind == "footnote":
            print(f"  p{b.page}    footnote: {b.text}  (section: {' > '.join(b.path)})")
        else:
            notes = f"  [notes: {', '.join(n[0] for n in b.notes)}]" if b.notes else ""
            print(f"  p{b.page}    {'- ' if b.kind == 'list_item' else ''}{b.text[:70]}{'...' if len(b.text) > 70 else ''}{notes}")
    truth = [s["text"] for s in d.truth.get("sections", []) if s["kind"] in ("p", "li")]
    if truth:
        got = {b.text for b in blocks if b.kind in ("paragraph", "list_item")}
        print(f"paragraphs and list items found word for word: {sum(1 for t in truth if t in got)} of {len(truth)}")


if __name__ == "__main__":
    main()
