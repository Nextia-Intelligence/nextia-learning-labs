"""Provenance: store where every value came from, and draw it back on the page.

    python -m doc_extract.provenance D011               # the text layer of a digital receipt
    python -m doc_extract.provenance D036 --path ocr    # OCR on a phone photo
    python -m doc_extract.provenance D056               # a table cell: page and box
    python -m doc_extract.provenance D057               # a spreadsheet cell: sheet and cell

Each value becomes a record: value, status, and its evidence (file, page, box and unit; or sheet
and cell). The picture with the boxes is written to out/evidence/.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import ImageDraw

from doc_extract import contract
from doc_extract.fields import Extraction, Found
from doc_extract.pages import Page

OUT = Path("out/evidence")
DRAW_DPI = 100


@dataclass
class Evidence:
    file: str
    page: int | None = None
    box: list[float] | None = None  # x0, top, x1, bottom
    unit: str = ""  # "pt" (1/72 inch, PDF pages) or "px" (pixels of the image file)
    sheet: str | None = None
    cell: str | None = None
    path: str = ""  # which path read it: text, ocr, vision, table, sheet
    seen: str = ""  # the text at that place


def _to_pt(box, page: Page) -> list[float]:
    """A box on a PDF page drawn at page.dpi -> points. Image files keep pixels."""
    if page.unit == "px" and page.dpi:
        return [round(v * 72 / page.dpi, 1) for v in box]
    return [round(v, 1) for v in box]


def evidence(f: Found, ex: Extraction) -> Evidence | None:
    if not f.lines:
        return None
    page = next((p for p in ex.pages if p.page == f.page), None)
    x0 = min(ln.box[0] for ln in f.lines)
    y0 = min(ln.box[1] for ln in f.lines)
    x1 = max(ln.box[2] for ln in f.lines)
    y1 = max(ln.box[3] for ln in f.lines)
    if page is None:
        return Evidence(ex.file, f.page, [x0, y0, x1, y1], "", path=ex.path, seen=f.raw)
    unit = "pt" if page.unit == "pt" or page.dpi else "px"
    return Evidence(ex.file, f.page, _to_pt((x0, y0, x1, y1), page), unit, path=ex.path, seen=f.raw)


def record(ex: Extraction) -> dict:
    """The extraction as stored: every field with its value, status and evidence."""
    out = {"file": ex.file, "path": ex.path, "contract": contract.CONTRACT_VERSION, "fields": {}}
    for name, f in ex.fields.items():
        ev = evidence(f, ex)
        out["fields"][name] = {"value": f.value, "status": f.status, "reason": f.reason or None,
                               "evidence": asdict(ev) if ev else None}
    return out


def draw(path: Path, ex: Extraction, target: Path) -> list[Path]:
    """Draw every field's box on its page and write one picture per page."""
    from doc_extract import files

    written = []
    pages = sorted({f.page for f in ex.fields.values() if f.lines}) or [1]
    for pg in pages:
        img = files.page_image(path, pg, DRAW_DPI)
        d = ImageDraw.Draw(img)
        for name, f in ex.fields.items():
            ev = evidence(f, ex)
            if not ev or ev.page != pg:
                continue
            k = DRAW_DPI / 72 if ev.unit == "pt" else 1.0
            x0, y0, x1, y1 = (v * k for v in ev.box)
            d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=(214, 40, 40), width=2)
            d.text((x1 + 5, y0), name, fill=(214, 40, 40))
        target.parent.mkdir(parents=True, exist_ok=True)
        out = target.with_name(f"{target.stem}-p{pg}.png")
        img.save(out)
        written.append(out)
    return written


def main(argv: list[str] | None = None) -> None:
    from doc_extract import compare, documents, files, sheets, tables

    ap = argparse.ArgumentParser(description="Show where every value came from.")
    ap.add_argument("doc")
    ap.add_argument("--path", choices=["text", "ocr"], help="for a receipt (default: text for a PDF, else ocr)")
    ap.add_argument("--json", action="store_true", help="print the stored record")
    args = ap.parse_args(argv)
    d = documents.get(args.doc)
    if d.kind == "spreadsheet":
        names, units, recs = sheets.read(d.path)
        for rec in recs[:4]:
            c = rec["Price each (CAD)"]
            print(f"{rec['SKU'].value}: price each {c.value} {units['Price each (CAD)']} <- {d.file}, sheet {c.sheet}, cell {c.cell}")
        cat = recs[1]["Category"]
        print(f"{recs[1]['SKU'].value}: category {cat.value} <- sheet {cat.sheet}, cell {cat.cell}, merged range {cat.merged}")
        return
    if d.kind == "price_list":
        t = tables.recover(d.path)
        for rec in t.rows[30:34]:
            c = rec["Price (CAD) / Each"]
            print(f"{rec['SKU'].value}: price each {c.value} CAD <- {d.file}, page {c.page}, box {[round(v) for v in c.box]} pt")
        return
    path = args.path or ("text" if files.is_pdf(d.path) and d.source != "scan_pdf" else "ocr")
    ex = compare.run(d, path)
    if args.json:
        print(json.dumps(record(ex), indent=2, ensure_ascii=False))
        return
    for name, f in ex.fields.items():
        ev = evidence(f, ex)
        where = f"page {ev.page}, box {[round(v) for v in ev.box]} {ev.unit}" if ev else "-"
        shown = f.value if f.value is not None else f"absent ({f.reason})"
        print(f"  {name:<15} {str(shown):<22} {f.status:<9} {where}")
    for p in draw(d.path, ex, OUT / f"{d.doc_id}-{path}.png"):
        print(f"boxes drawn on {p}")


if __name__ == "__main__":
    main()
