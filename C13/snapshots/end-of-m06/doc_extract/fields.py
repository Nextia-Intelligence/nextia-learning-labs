"""Fill the extraction contract from lines of text with simple rules (no model).

The same rules run on the lines of every path (the PDF text layer and OCR), so a comparison of the
paths compares how well each one reads, not the rules. The rules know Larkfield's two receipt
layouts (the till receipt and the online order confirmation), in English and French. They do not
know other shops' layouts: there, they find less (see combine.py).

Every value keeps the lines it came from: that is its evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from doc_extract import contract
from doc_extract.pages import Line, Page, row_text, rows

KNOWN_VENDORS = {"larkfield": "Larkfield"}
FRENCH = re.compile(r"\b(sous-total|tps|tvq|commande|montant|livraison|merci|caisse|paiement)\b", re.I)
TAX = re.compile(r"^(gst|hst|pst|qst|tps|tvq|tvh|sales tax|tax|taxes)\b")
TOTAL = re.compile(r"^(total|total \((cad|usd)\))")
SUBTOTAL = re.compile(r"^(sub-?total|sous-total)\b")
SHIPPING = re.compile(r"^(shipping|livraison)\b")
CURRENCY = re.compile(r"(?<![A-Z])(CAD|USD)(?![A-Z])")
# "3 x 24.95  74.85": group 2 is the unit price, one amount ("1 011,78" in French). The second
# choice keeps a line whose price OCR misread (no decimals) as an item, as before.
QTY_LINE = re.compile(r"^(\d{1,2})\s*[x×X*]\s*\$?\s*(\d{1,3}(?:[ ,.]\d{3})*[.,]\d{2}(?!\d)|\d[\d ,.]*)")


@dataclass
class Found:
    field: str
    value: str | None
    status: str = "found"  # found | inferred | absent
    reason: str = ""  # why absent or how inferred
    raw: str = ""
    lines: list[Line] = field(default_factory=list)
    page: int = 1
    confidence: float | None = None  # what a model said about itself (vision path only)

    @property
    def score(self) -> float:
        """The lowest reading score of the evidence lines (1.0 for the text layer)."""
        return min((ln.score for ln in self.lines), default=1.0)


@dataclass
class Extraction:
    file: str
    path: str  # text | ocr | vision | combined
    fields: dict[str, Found] = field(default_factory=dict)
    items: list[dict] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)
    seconds: float = 0.0
    notes: list[str] = field(default_factory=list)
    usage: dict = field(default_factory=dict)  # tokens and cost (vision path)

    def value(self, name: str) -> str | None:
        f = self.fields.get(name)
        return f.value if f else None


def _plain(s: str) -> str:
    return contract._plain(s).strip()


def _money_in(row: list[Line], skip_label: bool = True) -> tuple[str | None, list[Line]]:
    """The last amount on a row, and the lines that hold the label and the amount."""
    text = row_text(row[1:] if skip_label and len(row) > 1 else row)
    if skip_label and len(row) == 1:
        text = re.sub(r"^[^\d$]*", "", row[0].text)
    v = contract.money(text)
    return v, row


def extract(pages: list[Page], path: str) -> Extraction:
    """Apply the rules to the pages of one document."""
    out = Extraction(pages[0].file if pages else "", path, pages=pages,
                     seconds=round(sum(p.seconds for p in pages), 3))
    all_rows: list[tuple[int, list[Line]]] = [(p.page, r) for p in pages for r in rows(p.lines)]
    text = "\n".join(row_text(r) for _, r in all_rows)
    french = bool(FRENCH.search(text)) or " QC " in f" {text} "
    found: dict[str, Found] = {}

    def put(name: str, value: str | None, page: int, lines: list[Line], raw: str, status: str = "found", reason: str = ""):
        if value is not None and name not in found:
            found[name] = Found(name, value, status, reason, raw, list(lines), page)

    for i, (page, row) in enumerate(all_rows):
        t = row_text(row)
        p = _plain(t)
        if i < 2 and "vendor" not in found:  # the shop's name is printed at the top
            for key, name in KNOWN_VENDORS.items():
                if key in p:
                    put("vendor", name, page, [row[0]], row[0].text)
        on = contract.order_number(t)
        if on:
            put("order_number", on, page, row, t)
        if "date" not in found and not re.match(r"^(due|valid)", p):
            d = contract.parse_date(t, day_first=french)
            if d:
                put("date", d, page, row, t)
        if SUBTOTAL.match(p):
            v, ev = _money_in(row)
            put("subtotal", v, page, ev, t)
        elif SHIPPING.match(p):
            v, ev = _money_in(row)
            put("shipping", v, page, ev, t)
        elif TOTAL.match(p) and "total" not in found:
            v, ev = _money_in(row)
            if v is None and i + 1 < len(all_rows):  # the amount printed on the next row
                nxt = all_rows[i + 1][1]
                v = contract.money(row_text(nxt))
                ev = row + nxt
                t = t + " " + row_text(nxt)
            put("total", v, page, ev, t)
            m = CURRENCY.search(t.upper())
            if m:
                put("currency", m[1], page, ev, t)
            elif "$" in t:
                put("currency", "CAD", page, ev, t, "inferred", "a '$' sign at a shop in Canada")
        elif TAX.match(p):
            v, _ = _money_in(row)
            if v is not None:
                f = found.get("tax")
                if f is None:
                    put("tax", v, page, row, t)
                else:  # add every tax line (GST + PST, TPS + TVQ)
                    f.value = f"{float(f.value) + float(v):.2f}"
                    f.lines += row
                    f.raw += " + " + t
        if "payment_method" not in found and ("total" in found or re.match(r"^(payment|paiement)", p)):
            pm = contract.payment(t)
            if pm:
                put("payment_method", pm, page, row, t)
    if "vendor" not in found and all_rows and not re.search(r"\d", row_text(all_rows[0][1])):
        page, row = all_rows[0]  # an unknown shop: its name is usually the first printed row
        put("vendor", row_text(row), page, row, row_text(row), "found", "unknown shop: the first printed line")
    if "currency" not in found:
        m = CURRENCY.search(text.upper())
        if m:
            row = next(((pg, r) for pg, r in all_rows if m[1] in row_text(r).upper()), None)
            if row:
                put("currency", m[1], row[0], row[1], row_text(row[1]))
        else:
            addr = next(((pg, r) for pg, r in all_rows if re.search(r"\b(ON|QC|BC|AB|NS|MB)\b", row_text(r))), None)
            if addr:
                put("currency", "CAD", addr[0], addr[1], row_text(addr[1]), "inferred", "a shop address in Canada")
    for spec in contract.RECEIPT:
        if spec.name not in found:
            found[spec.name] = Found(spec.name, None, "absent", "not_found")
    out.fields = {spec.name: found[spec.name] for spec in contract.RECEIPT}
    out.items = items(all_rows)
    return out


def items(all_rows: list[tuple[int, list[Line]]]) -> list[dict]:
    """The item lines of Larkfield's two layouts: a description row then 'q x price  total' (till),
    or one table row 'description  qty  unit price  amount' (online order)."""
    out = []
    for i, (page, row) in enumerate(all_rows):
        t = row_text(row)
        m = QTY_LINE.match(t.strip())
        if m and i > 0:
            amounts = [contract.money(ln.text) for ln in row if contract.money(ln.text)]
            desc_row = all_rows[i - 1][1]
            if len(amounts) >= 1 and not contract.money(row_text(desc_row)):
                unit = contract.money(m[2])
                out.append({"description": row_text(desc_row), "quantity": int(m[1]), "unit_price": unit,
                            "line_total": amounts[-1], "page": page, "lines": desc_row + row})
            continue
        if len(row) >= 4 and re.fullmatch(r"\d{1,2}", row[-3].text.strip()):
            unit, total = contract.money(row[-2].text), contract.money(row[-1].text)
            if unit and total:
                out.append({"description": " ".join(ln.text for ln in row[:-3]), "quantity": int(row[-3].text),
                            "unit_price": unit, "line_total": total, "page": page, "lines": row})
    return out
