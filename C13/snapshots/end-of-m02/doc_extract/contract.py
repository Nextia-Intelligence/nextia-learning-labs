"""The extraction contract: what Larkfield needs from a receipt, in which format, with which evidence,
and which values may be missing (and why).

    python -m doc_extract.contract

Every extracted value is a record with a status:
  found       printed on the document; the evidence says where (file, page, box)
  inferred    not printed, but follows from something printed (the evidence points to that)
  absent      not on the document; `reason` says why (not_printed, cut_off, unreadable)
A value is never guessed. "absent" is a correct answer when the document does not show the value.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

CONTRACT_VERSION = "receipt-v1"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: str  # text, code, date, money, enum
    format: str
    required: bool
    may_be_missing: tuple[str, ...]  # the reasons a value may be absent
    notes: str = ""


RECEIPT = (
    FieldSpec("vendor", "text", "the shop's name, e.g. Larkfield", True, ("unreadable",)),
    FieldSpec("order_number", "code", "LK- and 6 digits, e.g. LK-547562", False, ("not_printed", "cut_off", "unreadable"),
              "In-store receipts have a transaction number instead. Never put the transaction number here."),
    FieldSpec("date", "date", "YYYY-MM-DD (ISO 8601)", True, ("cut_off", "unreadable"),
              "Receipts from Quebec print the day first: 09/08/2026 is 9 August 2026."),
    FieldSpec("currency", "code", "CAD or USD (ISO 4217)", True, ("unreadable",),
              "A shop in Canada that prints only '$' or no symbol: CAD, with status inferred."),
    FieldSpec("subtotal", "money", "2 decimals, a point, no thousands separator: 1011.78", True, ("cut_off", "unreadable")),
    FieldSpec("shipping", "money", "2 decimals", False, ("not_printed", "cut_off", "unreadable"),
              "Till receipts have no shipping line: absent, not_printed (counts as 0.00)."),
    FieldSpec("tax", "money", "2 decimals: the sum of all tax lines (GST, HST, PST, QST)", True, ("cut_off", "unreadable")),
    FieldSpec("total", "money", "2 decimals: the amount paid", True, ("cut_off", "unreadable")),
    FieldSpec("payment_method", "enum", "Visa, Mastercard, Amex, Debit or Cash (no card number)", False,
              ("not_printed", "cut_off", "unreadable")),
)
ITEM = (
    FieldSpec("description", "text", "as printed", True, ()),
    FieldSpec("quantity", "number", "a whole number", True, ()),
    FieldSpec("unit_price", "money", "2 decimals", True, ()),
    FieldSpec("line_total", "money", "2 decimals", True, ()),
)
FIELDS = {f.name: f for f in RECEIPT}
EVIDENCE = "file, page and box (x0, top, x1, bottom) in the page's unit; for a spreadsheet, sheet and cell"
PAYMENTS = {"visa": "Visa", "mastercard": "Mastercard", "amex": "Amex", "debit": "Debit", "cash": "Cash"}
MONTHS = {
    "jan": 1, "january": 1, "janv": 1, "janvier": 1, "feb": 2, "february": 2, "fevr": 2, "fevrier": 2,
    "mar": 3, "march": 3, "mars": 3, "apr": 4, "april": 4, "avr": 4, "avril": 4, "may": 5, "mai": 5,
    "jun": 6, "june": 6, "juin": 6, "jul": 7, "july": 7, "juil": 7, "juillet": 7, "aug": 8, "august": 8,
    "aout": 8, "sep": 9, "sept": 9, "september": 9, "septembre": 9, "oct": 10, "october": 10, "octobre": 10,
    "nov": 11, "november": 11, "novembre": 11, "dec": 12, "december": 12, "decembre": 12,
}


def _plain(s: str) -> str:
    """Lower case, without accents: 'Févr.' -> 'fevr.'"""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


MONEY = re.compile(r"(?<![\d,.])(\d{1,3}(?:[   ,.]\d{3})*|\d+)([.,]\d{2})(?!\d)")


def money(raw: str | None) -> str | None:
    """'1 011,78 $' -> '1011.78'; 'CAD 1,011.78' -> '1011.78'; '$178.54' -> '178.54'. None if no amount."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)) or re.fullmatch(r"\s*\d+(\.\d{1,2})?\s*", str(raw)):
        return f"{float(raw):.2f}"  # a plain number (a model may answer 189 or 74.4)
    found = list(MONEY.finditer(str(raw)))
    m = found[-1] if found else None  # the last amount on the line
    if not m:
        return None
    whole = re.sub(r"[   ,.]", "", m.group(1))
    return f"{int(whole)}.{m.group(2)[1:]}"


def parse_date(raw: str | None, day_first: bool = False) -> str | None:
    """A printed date -> 'YYYY-MM-DD'. day_first: 09/08/2026 is 9 August (Quebec), not 8 September."""
    if not raw:
        return None
    s = _plain(raw)
    m = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    try:
        if m:
            return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        m = re.search(r"(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(20\d{2})", s)
        if m:
            a, b, y = int(m[1]), int(m[2]), int(m[3])
            d, mo = (a, b) if day_first else (b, a)
            return date(y, mo, d).isoformat()
        m = re.search(r"([a-z]+)\.?\s+(\d{1,2}),?\s*(20\d{2})", s)  # September 14, 2026 / Sep 14 2026
        if m and m[1] in MONTHS:
            return date(int(m[3]), MONTHS[m[1]], int(m[2])).isoformat()
        m = re.search(r"(\d{1,2})\s+([a-z]+)\.?\s+(20\d{2})", s)  # 14 sept. 2026
        if m and m[2] in MONTHS:
            return date(int(m[3]), MONTHS[m[2]], int(m[1])).isoformat()
    except ValueError:
        return None
    return None


def order_number(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.search(r"LK\s*[-–]\s*(\d{6})(?!\d)", raw.upper())
    return f"LK-{m[1]}" if m else None


def payment(raw: str | None) -> str | None:
    if not raw:
        return None
    for word in re.findall(r"[a-z]+", _plain(raw)):
        if word in PAYMENTS:
            return PAYMENTS[word]
    return None


# The shops whose receipts Larkfield accepts, with the ways their names are printed.
VENDORS = {"Larkfield": ("larkfield",), "Maple & Pine Hardware": ("maple & pine", "maple and pine", "maple pine")}


def vendor(raw: str | None) -> str | None:
    """The registered name of the shop named in the text, or the text itself if no shop matches."""
    if not raw:
        return None
    plain = _plain(raw)
    for name, aliases in VENDORS.items():
        if any(a in plain for a in aliases):
            return name
    return re.sub(r"\s+", " ", raw).strip()


def normalise(field: str, value) -> str | None:
    """The form used to compare two values of a field: the same value, written the same way."""
    if value is None or value == "":
        return None
    v = str(value).strip()
    if (field in FIELDS and FIELDS[field].kind == "money") or field in ("unit_price", "line_total"):
        return money(v)
    if field == "date":
        return parse_date(v) or v
    if field == "order_number":
        return order_number(v) or v.upper()
    if field == "payment_method":
        return payment(v) or v
    if field == "currency":
        return v.upper()
    if field == "vendor":
        v = vendor(v) or v
    s = _plain(v)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def main() -> None:
    print(f"Extraction contract {CONTRACT_VERSION}: one record per receipt")
    print(f"Evidence for every found or inferred value: {EVIDENCE}\n")
    print(f"{'field':<15} {'kind':<6} {'required':<9} {'may be missing because':<34} format")
    for f in RECEIPT:
        print(f"{f.name:<15} {f.kind:<6} {'yes' if f.required else 'no':<9} {', '.join(f.may_be_missing) or '-':<34} {f.format}")
        if f.notes:
            print(f"{'':<15} {f.notes}")
    print("\nitems: a list, one entry per printed line: " + ", ".join(f"{f.name} ({f.format})" for f in ITEM))


if __name__ == "__main__":
    main()
