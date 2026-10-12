"""Tables in a PDF: one table that continues on the next page, with merged cells.

    python -m doc_extract.tables D056            # the supplier price list
    python -m doc_extract.tables D056 --naive    # page by page, as the PDF library returns it

The price list has the problems a real one has:
  - the header has two rows, and "Price (CAD)" is one merged cell over "Each" and "Case of 6";
  - the category is printed once per group: one merged cell over several rows;
  - the table continues on page 2, where the header is printed again and the category is
    printed again as "Sprinklers (cont.)".
recover() returns one table: one record per product, each cell with its page and box.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pdfplumber


@dataclass
class Cell:
    value: str | None
    page: int
    box: tuple[float, float, float, float] | None  # in points; for a filled cell, the merged cell's box
    filled: bool = False  # True when the value comes from a merged cell above or to the left


@dataclass
class Table:
    columns: list[str]
    units: dict[str, str]
    rows: list[dict[str, Cell]]
    header_rows: int
    pages: list[int]


def raw_tables(path: Path) -> list[tuple[int, list[list[str | None]], list[list[tuple | None]]]]:
    """Every table the PDF library finds: (page, cell texts, cell boxes), page by page."""
    out = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            for t in p.find_tables():
                texts = t.extract()
                boxes = [list(r.cells) for r in t.rows]
                out.append((p.page_number, texts, boxes))
    return out


def _header_rows(tables) -> int:
    """How many top rows are the same on every page: those rows are the header."""
    if len(tables) < 2:
        return 1
    n = 0
    first = tables[0][1]
    while all(len(t[1]) > n and t[1][n] == first[n] for t in tables[1:]) and n < len(first) - 1:
        n += 1
    return max(n, 1)


def column_names(header: list[list[str | None]]) -> list[str]:
    """Join the header rows into one name per column. An empty cell in the first row belongs to the
    merged cell on its left; an empty cell in a lower row belongs to the merged cell above it."""
    width = len(header[0])
    grid = [list(r) for r in header]
    for c in range(1, width):
        if grid[0][c] is None:
            grid[0][c] = grid[0][c - 1]
    for r in range(1, len(grid)):
        for c in range(width):
            if grid[r][c] is None:
                grid[r][c] = grid[r - 1][c]
    names = []
    for c in range(width):
        parts: list[str] = []
        for r in range(len(grid)):
            if grid[r][c] and grid[r][c] not in parts:
                parts.append(grid[r][c])
        names.append(" / ".join(parts))
    return names


def unit_of(name: str) -> str | None:
    m = re.search(r"\(([A-Za-z]{1,4})\)", name)
    return m[1] if m else None


def recover(path: Path) -> Table:
    tables = raw_tables(path)
    if not tables:
        raise SystemExit(f"{path.name}: no table found")
    n_head = _header_rows(tables)
    columns = column_names(tables[0][1][:n_head])
    units = {c: u for c in columns if (u := unit_of(c))}
    rows: list[dict[str, Cell]] = []
    above: dict[int, Cell] = {}
    for page, texts, boxes in tables:
        for r_i in range(n_head, len(texts)):  # the header is printed again on every page: skip it
            rec: dict[str, Cell] = {}
            for c_i, name in enumerate(columns):
                text = texts[r_i][c_i]
                box = boxes[r_i][c_i] if c_i < len(boxes[r_i]) else None
                if text is None and box is None and c_i in above:  # inside a merged cell: take its value
                    cell = Cell(above[c_i].value, above[c_i].page, above[c_i].box, True)
                else:
                    value = None if text in (None, "", "n/a") else re.sub(r"\s*\(cont\.\)$", "", text.replace("\n", " "))
                    cell = Cell(value, page, tuple(box) if box else None)
                    above[c_i] = cell
                rec[name] = cell
            rows.append(rec)
    return Table(columns, units, rows, n_head, sorted({t[0] for t in tables}))


def naive(path: Path) -> list[list[str | None]]:
    """What a quick look gives: every row of every page, as the library returns it."""
    return [row for _, texts, _ in raw_tables(path) for row in texts]


TRUTH_COLUMNS = {"category": "Category", "sku": "SKU", "description": "Description", "unit": "Unit",
                 "price_each_cad": "Price (CAD) / Each", "price_case_cad": "Price (CAD) / Case of 6"}


def score(table_rows: list[dict[str, str | None]], truth_rows: list[dict]) -> tuple[int, int]:
    """(correct cells, true cells): every truth row is looked up by its SKU."""
    by_sku = {r.get("SKU"): r for r in table_rows}
    ok = total = 0
    for t in truth_rows:
        got = by_sku.get(t["sku"], {})
        for key, col in TRUTH_COLUMNS.items():
            total += 1
            ok += (got.get(col) or None) == (t[key] or None)
    return ok, total


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents

    argv = sys.argv[1:] if argv is None else argv
    d = documents.get(argv[0] if argv else "D056")
    truth = d.truth.get("rows", [])
    if "--naive" in argv:
        rows = naive(d.path)
        for r in rows[:5] + [["..."]] + rows[30:36]:
            print("  ", r)
        header = rows[0]
        as_dicts = [{(h or f"col{i}"): v for i, (h, v) in enumerate(zip(header, r))} for r in rows[1:]]
        ok, total = score([{("Price (CAD) / Each" if k == "Price (CAD)" else k): v for k, v in r.items()} for r in as_dicts], truth)
        print(f"{len(rows)} rows (header rows counted as data), cells correct: {ok} of {total} ({ok / total:.0%})")
        return
    t = recover(d.path)
    print(f"{d.file}: one table on pages {t.pages}, {t.header_rows} header rows, {len(t.rows)} products")
    print(f"columns: {t.columns}")
    print(f"units from the header: {t.units}")
    for rec in t.rows[30:36]:
        cells = ", ".join(f"{k.split(' / ')[-1]}={c.value}{'*' if c.filled else ''} (p{c.page})" for k, c in rec.items())
        print(f"  {cells}")
    print("  (* = from a merged cell; the box is the merged cell's box)")
    plain = [{k: c.value for k, c in r.items()} for r in t.rows]
    ok, total = score(plain, truth)
    print(f"cells correct: {ok} of {total} ({ok / total:.0%})")


if __name__ == "__main__":
    main()
