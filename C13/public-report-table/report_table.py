"""Recover a statistics table that spans two pages, keep the place of every cell, and check it
against the agency's CSV files.

Case study "Extract a table from a public report" (Document and Multimodal AI, Nextia Learning).
The table: USDA NASS *Crop Production*, "Crop Area Planted and Harvested, Yield, and Production
in Domestic Units - United States". Page 1 has the area columns, page 2 continues the same rows
with the unit, the yield and the production columns.

Only pdfplumber and the standard library. Run as a script for a summary:

    python report_table.py crop0926.pdf crop0926.zip

Boxes are in PDF points from the top-left corner of the page: [x0, top, x1, bottom].
"""

from __future__ import annotations

import csv
import io
import re
import sys
import zipfile
from dataclasses import dataclass, field

import pdfplumber

TITLE = "Crop Area Planted and Harvested, Yield, and Production in Domestic Units"
CODES = {"(NA)": "NA", "(X)": "X", "(D)": "D", "(Z)": "Z"}  # codes printed in place of a number
MARK_SIZE = 6.0  # footnote marks are printed smaller than this (5 pt, against 8 pt for the text)


@dataclass
class Cell:
    """One cell of the recovered table, with its place on the page."""

    text: str  # as printed ("2,299", "(NA)", "" for a blank cell)
    page: int | None = None  # page number in the PDF, from 1
    box: list[float] | None = None  # [x0, top, x1, bottom] in points; for a blank cell: the empty slot
    unit: str | None = None

    @property
    def blank(self) -> bool:
        return self.text == ""

    @property
    def code(self) -> str | None:
        return CODES.get(self.text)

    @property
    def number(self) -> float | None:
        return to_number(self.text)


@dataclass
class Row:
    label: str  # the crop, without its footnote marks
    group: str  # the bold group row above it, such as "Grains and hay"
    parent: str  # the row it is indented under ("Hay, all" for "Alfalfa"), or ""
    marks: list[str] = field(default_factory=list)  # footnote marks printed after the label
    unit: str = ""  # the unit printed in the label column (page 2), such as "bushels"
    cells: dict[str, Cell] = field(default_factory=dict)  # column name -> cell

    @property
    def key(self) -> tuple[str, str]:
        return (self.parent, self.label)


@dataclass
class Table:
    pages: list[int]
    columns: list[str]
    rows: list[Row]
    footnotes: dict[str, str]  # mark or code -> its text
    units: dict[str, str]  # column -> unit from the header


def to_number(text: str) -> float | None:
    """'2,299' -> 2299.0, '–0.5' -> -0.5; None for a code or a blank."""
    t = text.replace(",", "").replace("–", "-").replace("−", "-").strip()
    try:
        return float(t)
    except ValueError:
        return None


def find_pages(pdf, title: str = TITLE) -> list[int]:
    """The pages whose title starts with `title`: the first page and its '(continued)' pages."""
    found = []
    for n, page in enumerate(pdf.pages, 1):
        top = " ".join((page.extract_text() or "").splitlines()[:2])
        if top.startswith(title):
            found.append(n)
    return found


def table_rules(page):
    """The table's printed lines: the x of each vertical rule, and the table's top, body and bottom."""
    thin_v = [r for r in page.rects if r["width"] < 2 and r["height"] > 1]
    thin_h = [r for r in page.rects if r["height"] < 2 and r["width"] > 50]
    long_v = [r for r in thin_v if r["height"] > 100]  # the rules that run down the body
    xs = sorted({round((r["x0"] + r["x1"]) / 2) for r in long_v})
    merged = []
    for x in xs:  # one rule can be drawn as two thin rectangles side by side
        if not merged or x - merged[-1] > 2:
            merged.append(x)
    left = min(r["x0"] for r in thin_h)
    right = max(r["x1"] for r in thin_h)
    return {
        "edges": [left, *merged, right],  # label column, then one column between each pair
        "head_top": min(r["top"] for r in thin_v),
        "body_top": min(r["top"] for r in long_v),
        "body_bottom": max(r["bottom"] for r in long_v),
    }


def _lines(words):
    """Group words into printed lines by their top; small footnote marks join the nearest line."""
    normal = sorted((w for w in words if w["size"] >= MARK_SIZE), key=lambda w: (w["top"], w["x0"]))
    lines: list[list[dict]] = []
    for w in normal:
        if lines and abs(lines[-1][0]["top"] - w["top"]) < 2:
            lines[-1].append(w)
        else:
            lines.append([w])
    for m in (w for w in words if w["size"] < MARK_SIZE):
        near = min(lines, key=lambda ln: abs(ln[0]["top"] - m["top"]), default=None)
        if near is not None and abs(near[0]["top"] - m["top"]) < 3:
            near.append(m)
    return [sorted(ln, key=lambda w: w["x0"]) for ln in lines]


def _box(words) -> list[float]:
    return [round(min(w["x0"] for w in words), 1), round(min(w["top"] for w in words), 1),
            round(max(w["x1"] for w in words), 1), round(max(w["bottom"] for w in words), 1)]


def _phrases(words, gap=6.0):
    """Join words that stand close together on one line into phrases ("Area planted")."""
    out: list[list[dict]] = []
    for w in sorted(words, key=lambda w: w["x0"]):
        if out and w["x0"] - out[-1][-1]["x1"] < gap:
            out[-1].append(w)
        else:
            out.append([w])
    return out


def read_page(page, n: int):
    """One page of the table: its column names and units (from the header) and its rows."""
    r = table_rules(page)
    edges = r["edges"]
    spans = list(zip(edges[1:-1], edges[2:]))  # the data columns, left to right
    words = page.extract_words(extra_attrs=["size", "fontname"])

    # 1. The header: a phrase belongs to every column it crosses ("Area planted" covers two years).
    parts: list[list[str]] = [[] for _ in spans]
    units: list[str | None] = [None for _ in spans]
    head = [w for w in words if r["head_top"] - 1 <= w["top"] < r["body_top"] and w["x0"] >= edges[1] - 1]
    for line in _lines(head):
        for ph in _phrases(line):
            text = " ".join(w["text"] for w in ph)
            x0, x1 = ph[0]["x0"], ph[-1]["x1"]
            for i, (a, b) in enumerate(spans):
                if x0 < b and x1 > a:
                    if text.startswith("(") and text.endswith(")"):
                        units[i] = text[1:-1]  # "(1,000 acres)" is the unit of that column
                    else:
                        parts[i].append(text)
    columns = [" / ".join(p) for p in parts]

    # 2. The body: one printed line is one row.
    body = [w for w in words if r["body_top"] <= w["top"] < r["body_bottom"]]
    rows = []
    label_x = min((w["x0"] for w in body if w["x1"] <= edges[1]), default=edges[0])
    for line in _lines(body):
        in_label = [w for w in line if w["x1"] <= edges[1] + 1]
        text_words = [w for w in in_label if w["size"] >= MARK_SIZE]
        marks = [w["text"] for w in in_label if w["size"] < MARK_SIZE]
        joined = " ".join(w["text"] for w in text_words)
        label, _, after = joined.partition("...")  # the leader dots end the label
        label, unit = label.strip(), after.strip(" .")
        label_words = [w for w in text_words if not w["text"].startswith("...")]
        cells = {}
        for name, unit_col, (a, b) in zip(columns, units, spans):
            inside = [w for w in line if a <= (w["x0"] + w["x1"]) / 2 < b]
            if inside:
                cells[name] = Cell(" ".join(w["text"] for w in inside), n, _box(inside), unit_col)
            else:  # a blank cell: keep the empty slot as its place
                top, bottom = min(w["top"] for w in line), max(w["bottom"] for w in line)
                cells[name] = Cell("", n, [round(a, 1), round(top, 1), round(b, 1), round(bottom, 1)], unit_col)
        bold = all("Bold" in w["fontname"] for w in text_words) if text_words else False
        rows.append({
            "label": label, "unit": unit, "marks": marks, "cells": cells, "bold": bold,
            "indent": bool(label_words) and label_words[0]["x0"] > label_x + 4,
            "label_box": _box(label_words) if label_words else None,
            "unit_box": _box([w for w in text_words if w["text"].strip(".").endswith(unit)][-1:]) if unit else None,
        })

    # 3. The notes under the table: codes such as "(NA) Not available." and marks such as "1 Area ...".
    notes = {}
    below = [w for w in words if r["body_bottom"] < w["top"] < page.height - 60]
    for line in _lines(below):
        first, rest = line[0], " ".join(w["text"] for w in line[1:])
        if first["text"] in CODES:
            notes[first["text"]] = rest
        elif first["size"] < MARK_SIZE and first["text"].isdigit():
            notes[first["text"]] = rest
    return columns, dict(zip(columns, units)), rows, notes


def read_table(path: str, title: str = TITLE) -> Table:
    """Find the table by its title, read each of its pages and join them into one table.

    Page 2 continues page 1 to the right: the same rows, more columns. Rows are joined by their
    label and the row they are indented under. Bold rows without numbers are groups: their name
    is filled into every row below them, like a merged category cell."""
    with pdfplumber.open(path) as pdf:
        pages = find_pages(pdf, title)
        if not pages:
            raise SystemExit(f"No table titled {title!r} in {path}")
        table = Table(pages, [], [], {}, {})
        by_key: dict[tuple[str, str], Row] = {}
        for n in pages:
            columns, units, rows, notes = read_page(pdf.pages[n - 1], n)
            table.footnotes.update(notes)
            if any(r["unit"] for r in rows):
                table.columns.append("Unit")
            table.columns += columns
            table.units.update({c: u for c, u in units.items() if u})
            group = parent = ""
            for r in rows:
                if not r["label"]:
                    continue
                if r["bold"] and all(c.blank for c in r["cells"].values()):
                    group, parent = r["label"], ""
                    continue
                key_parent = parent if r["indent"] else ""
                if not r["indent"]:
                    parent = r["label"]
                row = by_key.get((key_parent, r["label"]))
                if row is None:
                    row = by_key[(key_parent, r["label"])] = Row(r["label"], group, key_parent)
                    table.rows.append(row)
                row.marks += [m for m in r["marks"] if m not in row.marks]
                if r["unit"]:
                    row.unit = r["unit"]
                    row.cells["Unit"] = Cell(r["unit"], n, r["unit_box"])
                row.cells.update(r["cells"])
    for row in table.rows:  # units that depend on the row: "bushels per acre", "1,000 bushels"
        yield_unit = next((m.group(1) for k in row.marks
                           if (m := re.match(r"Yield in (\w+)", table.footnotes.get(k, "")))), row.unit)
        for name, cell in row.cells.items():
            if name.startswith("Yield per "):  # "Yield per acre / 2025": the unit is "<unit> per acre"
                per = name.split(" / ")[0].removeprefix("Yield per ")
                cell.unit = f"{cell.unit or yield_unit} per {per}"
            elif row.unit and cell.unit == "1,000":
                cell.unit = f"1,000 {row.unit}"
    return table


# --- Other ways to read the same pages, for the comparison ---------------------------------------

def _rows_from_lines(items, page_no, columns_by_page):
    """Turn (label column text, [value texts]) pairs into Rows; the label ends at the leader dots."""
    rows = []
    for label_text, values in items:
        label, _, after = label_text.partition("...")
        label, unit = label.strip(), after.strip(" .")
        row = Row(label, "", "")
        names = columns_by_page[page_no]
        if unit:
            row.unit = unit
            row.cells["Unit"] = Cell(unit, page_no)
        for name, value in zip(names, values):
            row.cells[name] = Cell(value or "", page_no)
        rows.append(row)
    return rows


def _join_by_label(parts):
    joined: dict[str, Row] = {}
    for rows in parts:
        for r in rows:
            if r.label in joined:
                joined[r.label].cells.update(r.cells)
                joined[r.label].marks += [m for m in r.marks if m not in joined[r.label].marks]
            else:
                joined[r.label] = r
    return list(joined.values())


def read_text_lines(path: str, columns_by_page: dict[int, list[str]], title: str = TITLE) -> list[Row]:
    """The quick way: the page as plain text, one line per row, the values split at the spaces and
    given to the columns from left to right."""
    parts = []
    with pdfplumber.open(path) as pdf:
        for n in find_pages(pdf, title):
            items = []
            for line in (pdf.pages[n - 1].extract_text() or "").splitlines():
                if "..." not in line:
                    continue
                left, dots, right = line.partition("...")
                right = right.strip(" .").split()
                unit = []
                if right and right[0].isalpha():  # page 2 prints the unit first
                    unit = [right.pop(0)]
                items.append((left + dots + " ".join(unit), right))
            parts.append(_rows_from_lines(items, n, columns_by_page))
    return _join_by_label(parts)


def read_library(path: str, columns_by_page: dict[int, list[str]], settings: dict | None = None,
                 title: str = TITLE) -> list[Row]:
    """The PDF library's own table finder, with its default settings or with `settings`."""
    parts = []
    with pdfplumber.open(path) as pdf:
        for n in find_pages(pdf, title):
            page = pdf.pages[n - 1]
            s = dict(settings or {})
            if s.pop("outer_edges", False):  # add the table's left and right edges as column lines
                r = table_rules(page)
                s["explicit_vertical_lines"] = [r["edges"][0], r["edges"][-1]]
            grid = page.extract_table(s) or []
            items = [(row[0] or "", row[1:]) for row in grid if row and row[0] and "..." in row[0]]
            # page 2 prints the unit inside the label column, after the dots: it stays in the label text
            parts.append(_rows_from_lines(items, n, columns_by_page))
    return _join_by_label(parts)


def read_vision(jsonl_path: str, columns_by_page: dict[int, list[str]], file: str | None = None,
                run: str = "pass1") -> list[Row]:
    """The vision model's recorded answers (one JSON line per page): its rows, joined by label.
    The model gives values, not places: its cells have a page but no box."""
    import json

    parts = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if (file and rec["file"] != file) or rec.get("pass", "pass1") != run:
                continue
            rows = []
            for r in json.loads(rec["answer"])["rows"]:
                if not r["unit"] and all(v == "" for v in r["values"]):
                    continue  # a group row
                row = Row(r["label"].strip(), "", "", list(r["marks"]))
                if r["unit"]:
                    row.unit = r["unit"]
                    row.cells["Unit"] = Cell(r["unit"], rec["page"])
                for name, value in zip(columns_by_page[rec["page"]], r["values"]):
                    row.cells[name] = Cell(value, rec["page"])
                rows.append(row)
            parts.append(rows)
    return _join_by_label(parts)


# --- The agency's CSV files -------------------------------------------------------------------

@dataclass
class RefRow:
    label: str
    parent: str
    group: str
    marks: list[str]
    values: dict[str, str | None]  # column -> the CSV's text; None when the line is too short


def read_reference(zip_path: str, title: str = TITLE) -> tuple[list[str], list[RefRow], dict[str, str], dict[str, str]]:
    """Read the tables titled `title` from the agency's zip of CSV files and join their parts.

    The CSV format (crop_help.htm in the zip): the first value is the table number, the second the
    line type: t title, h header, u units, d data, c closing line, f footnote. The files are
    Windows-1252 text. Returns the columns, the rows, the footnotes and the units line, read by
    position as the file gives it."""
    parts = []
    with zipfile.ZipFile(zip_path) as z:
        for name in sorted(z.namelist()):
            if not re.match(r"crop_p\d+[a-z]?_t\d+\.csv$", name):
                continue
            lines = list(csv.reader(io.StringIO(z.read(name).decode("cp1252"))))
            titles = [ln[2] for ln in lines if len(ln) > 2 and ln[1] == "t"]
            if any(t.startswith(title) for t in titles):
                parts.append((name, lines))
    columns: list[str] = []
    rows: dict[tuple[str, str], RefRow] = {}
    order: list[tuple[str, str]] = []
    notes: dict[str, str] = {}
    units: dict[str, str] = {}
    for _, lines in parts:
        heads = [ln[2:] for ln in lines if ln[1] == "h"]
        width = max(len(h) for h in heads)
        names = []
        for i in range(1, width):
            words = [h[i] for h in heads if i < len(h) and h[i]]
            names.append(" / ".join(words) if words else "Unit")
        columns += names
        for ln in lines:
            if ln[1] == "u":
                units.update({n: u.strip("()") for n, u in zip(names, ln[3:]) if u})
        group = parent = ""
        for ln in lines:
            if ln[1] == "f" and len(ln) > 2:
                m = re.match(r"(\(\w+\)|\d+/)\s+(.*)", ln[2])
                if m:
                    notes[m.group(1).rstrip("/")] = m.group(2)
            if ln[1] != "d" or len(ln) < 3 or not ln[2].strip():
                continue
            raw = ln[2]
            vals = ln[3:] + [None] * (len(names) - len(ln[3:]))
            if all(not v for v in vals):
                group, parent = raw.strip(), ""
                continue
            marks = re.findall(r"(\d+)/", raw)
            label = re.sub(r"\s*\d+/", "", raw).strip()
            indent = raw.startswith(" ")
            key = (parent if indent else "", label)
            if not indent:
                parent = label
            if key not in rows:
                rows[key] = RefRow(label, key[0], group, [], {})
                order.append(key)
            rows[key].marks += [m for m in marks if m not in rows[key].marks]
            rows[key].values.update(dict(zip(names, vals)))
    return columns, [rows[k] for k in order], notes, units


# --- Cell by cell -------------------------------------------------------------------------------

def same(ours: str | None, theirs: str | None) -> bool:
    """Equal as the table means it: numbers by value, codes and words as text, blanks as blanks."""
    a, b = (ours or "").strip(), (theirs or "").strip()
    if not a or not b:
        return not a and not b
    na, nb = to_number(a), to_number(b)
    if na is not None and nb is not None:
        return abs(na - nb) < 1e-9
    return a.lower() == b.lower()


def compare(table_rows: list[Row], ref_rows: list[RefRow], columns: list[str]) -> list[dict]:
    """One result per reference cell: match, wrong (both have a value), missing (we have none),
    extra (we have a value where the agency has none)."""
    ours = {r.key: r for r in table_rows}
    by_label = {r.label: r for r in table_rows}  # for readers that do not know the indented rows
    out = []
    for ref in ref_rows:
        row = ours.get((ref.parent, ref.label)) or by_label.get(ref.label)
        for col in columns:
            theirs = ref.values.get(col)
            cell = row.cells.get(col) if row else None
            mine = cell.text if cell else None
            if row is None:
                outcome = "missing"  # the row was not found: none of its cells can be used
            elif same(mine, theirs):
                outcome = "match"
            elif not (mine or "").strip():
                outcome = "missing"
            elif not (theirs or "").strip():
                outcome = "extra"
            else:
                outcome = "wrong"
            out.append({"row": ref.label, "parent": ref.parent, "column": col, "ours": mine, "theirs": theirs,
                        "outcome": outcome, "page": cell.page if cell else None, "box": cell.box if cell else None})
    return out


def score(results: list[dict]) -> dict[str, int]:
    counts = {"match": 0, "wrong": 0, "missing": 0, "extra": 0}
    for r in results:
        counts[r["outcome"]] += 1
    counts["cells"] = len(results)
    return counts


# --- Checks that need no reference file ------------------------------------------------------------

def _half_step(text: str) -> float:
    """Half of the last printed digit: '80.0' -> 0.05, '2,299' -> 0.5 (the rounding of the value)."""
    t = text.replace(",", "")
    return 0.5 * 10 ** -(len(t.split(".")[1]) if "." in t else 0)


TO_PRODUCTION_UNIT = {("pounds", "cwt"): 1 / 100, ("pounds", "bales"): 1 / 480}  # a bale of cotton is 480 lb


def checks(table: Table) -> list[dict]:
    """Two checks from the table's own logic, for reports that have no CSV:
    - parts add up: a row's indented rows sum to it ("Alfalfa" + "All other" = "Hay, all");
    - production = area harvested x yield, after the units, within the rounding of the printed values.
    One result per check: the rows, the column, the two sides, the allowed difference and ok."""
    out = []
    children: dict[str, list[Row]] = {}
    for r in table.rows:
        if r.parent:
            children.setdefault(r.parent, []).append(r)
    by_label = {r.label: r for r in table.rows if not r.parent}
    for parent, kids in children.items():
        top = by_label[parent]
        for col in table.columns:
            if col == "Unit" or col.startswith("Yield"):
                continue
            cells = [top.cells[col]] + [k.cells[col] for k in kids]
            if any(c.number is None for c in cells):
                continue
            total = sum(c.number for c in cells[1:])
            allowed = sum(_half_step(c.text) for c in cells)
            out.append({"check": "parts add up", "row": parent, "column": col, "printed": cells[0].number,
                        "computed": round(total, 3), "allowed": round(allowed, 3),
                        "ok": abs(cells[0].number - total) <= allowed + 1e-9})
    for r in table.rows:
        for year in ("2025", "2026"):
            area, yld, prod = (r.cells.get(f"{c} / {year}") for c in ("Area harvested", "Yield per acre", "Production"))
            if not (area and yld and prod) or None in (area.number, yld.number, prod.number):
                continue
            y_unit = yld.unit.removesuffix(" per acre")
            p_unit = (prod.unit or "").removeprefix("1,000 ")
            factor = 1.0 if y_unit == p_unit else TO_PRODUCTION_UNIT.get((y_unit, p_unit))
            if factor is None:
                continue
            computed = area.number * yld.number * factor
            allowed = (area.number * _half_step(yld.text) + yld.number * _half_step(area.text)) * factor \
                + _half_step(prod.text)
            out.append({"check": "area x yield", "row": r.label, "column": f"Production / {year}",
                        "printed": prod.number, "computed": round(computed, 3), "allowed": round(allowed, 3),
                        "ok": abs(prod.number - computed) <= allowed + 1e-9})
    return out


def changes(old: Table, new: Table) -> list[dict]:
    """The cells whose printed value differs between two releases of the same table."""
    before = {r.key: r for r in old.rows}
    out = []
    for r in new.rows:
        o = before.get(r.key)
        for col, cell in r.cells.items():
            prev = o.cells.get(col) if o else None
            if prev is None or not same(prev.text, cell.text):
                out.append({"row": r.label, "column": col, "before": prev.text if prev else None,
                            "after": cell.text, "page": cell.page, "box": cell.box})
    return out


def main(argv: list[str]) -> None:
    pdf_path, zip_path = argv[0], argv[1]
    table = read_table(pdf_path)
    columns, ref_rows, _, _ = read_reference(zip_path)
    print(f"{pdf_path}: table on pages {table.pages}, {len(table.rows)} rows, {len(table.columns)} columns")
    print("columns:", table.columns)
    print("units from the header:", table.units)
    print("footnotes:", table.footnotes)
    s = score(compare(table.rows, ref_rows, columns))
    print(f"cells that match the agency's CSV: {s['match']} of {s['cells']}"
          f" (wrong {s['wrong']}, missing {s['missing']}, extra {s['extra']})")
    c = checks(table)
    print(f"checks without the CSV: {sum(x['ok'] for x in c)} of {len(c)} pass")


if __name__ == "__main__":
    main(sys.argv[1:])
