"""Business validation: the checks a careful agent makes before trusting a receipt.

    python -m doc_extract.validate D050       # the receipt whose total does not add up
    python -m doc_extract.validate --all      # every receipt, after combine.py

Errors stop the value from reaching an agent unchecked (the document goes to review);
warnings are shown to the reviewer.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from doc_extract import contract

TAX_RATES = (Decimal("0"), Decimal("0.05"), Decimal("0.12"), Decimal("0.13"), Decimal("0.14975"), Decimal("0.15"))
EARLIEST = date(2020, 1, 1)


@dataclass
class Problem:
    field: str
    rule: str
    message: str
    severity: str = "error"  # error | warning


def _dec(v) -> Decimal | None:
    try:
        return Decimal(str(v)) if v is not None else None
    except InvalidOperation:
        return None


def validate(values: dict[str, str | None], items: list[dict] | None = None, today: date | None = None) -> list[Problem]:
    """values: field -> normalised value (None when absent)."""
    today = today or date.today()
    out: list[Problem] = []
    for spec in contract.RECEIPT:
        if spec.required and values.get(spec.name) is None:
            out.append(Problem(spec.name, "required", f"{spec.name} is missing"))
    d = values.get("date")
    if d:
        try:
            day = date.fromisoformat(d)
            if day > today:
                out.append(Problem("date", "future", f"the date {d} is after today ({today})"))
            elif day < EARLIEST:
                out.append(Problem("date", "too_old", f"the date {d} is before {EARLIEST}", "warning"))
        except ValueError:
            out.append(Problem("date", "format", f"{d!r} is not a date YYYY-MM-DD"))
    money = {k: _dec(values.get(k)) for k in ("subtotal", "shipping", "tax", "total")}
    for k, v in money.items():
        if values.get(k) is not None and v is None:
            out.append(Problem(k, "format", f"{values.get(k)!r} is not an amount"))
        elif v is not None and (v < 0 or v != v.quantize(Decimal("0.01"))):
            out.append(Problem(k, "format", f"{v} is not a positive amount with 2 decimals"))
    sub, ship, tax, total = money["subtotal"], money["shipping"] or Decimal("0"), money["tax"], money["total"]
    if None not in (sub, tax, total):
        expected = sub + ship + tax
        if abs(expected - total) > Decimal("0.01"):
            out.append(Problem("total", "adds_up", f"subtotal {sub} + shipping {ship} + tax {tax} = {expected}, "
                                                   f"but the total is {total} (difference {total - expected:+})"))
    if None not in (sub, tax) and sub + ship > 0 and values.get("currency") == "CAD":
        rate = tax / (sub + ship)
        if not any(abs(rate - r) <= Decimal("0.003") for r in TAX_RATES):
            out.append(Problem("tax", "rate", f"tax is {rate:.2%} of the price: no Canadian sales tax has this rate", "warning"))
    cur = values.get("currency")
    if cur and cur not in ("CAD", "USD"):
        out.append(Problem("currency", "allowed", f"{cur} is not CAD or USD"))
    elif cur == "USD":
        out.append(Problem("currency", "foreign", "paid in US dollars: convert before a refund in CAD", "warning"))
    on = values.get("order_number")
    if on and not re.fullmatch(r"LK-\d{6}", on):
        out.append(Problem("order_number", "format", f"{on!r} is not LK- and 6 digits"))
    pm = values.get("payment_method")
    if pm and pm not in contract.PAYMENTS.values():
        out.append(Problem("payment_method", "allowed", f"{pm!r} is not a known payment method"))
    if items and sub is not None:
        lines = [_dec(i.get("line_total")) for i in items]
        if None not in lines and abs(sum(lines) - sub) > Decimal("0.01"):
            out.append(Problem("items", "adds_up", f"the item lines add up to {sum(lines)}, the subtotal is {sub}", "warning"))
        for i in items:
            q, u, t = i.get("quantity"), _dec(i.get("unit_price")), _dec(i.get("line_total"))
            if q and u is not None and t is not None and abs(q * u - t) > Decimal("0.01"):
                out.append(Problem("items", "line", f"{q} x {u} is not {t} ({i.get('description')})", "warning"))
    return out


def duplicates(records: dict[str, dict[str, str | None]]) -> dict[str, str]:
    """Documents that show the same receipt as an earlier one: same order number, or the same
    shop, date and total. Returns {later document: earlier document}."""
    seen: dict[tuple, str] = {}
    out = {}
    for doc_id, v in records.items():
        keys = []
        if v.get("order_number"):
            keys.append(("order", v["order_number"]))
        if v.get("date") and v.get("total"):
            keys.append(("day-total", contract.normalise("vendor", v.get("vendor") or ""), v["date"], v["total"]))
        hit = next((seen[k] for k in keys if k in seen), None)
        if hit:
            out[doc_id] = hit
        for k in keys:
            seen.setdefault(k, doc_id)
    return out


def values_of(ex) -> dict[str, str | None]:
    return {n: contract.normalise(n, f.value) if n not in ("vendor",) else f.value for n, f in ex.fields.items()}


def main(argv: list[str] | None = None) -> None:
    from doc_extract import combine, documents

    argv = sys.argv[1:] if argv is None else argv
    docs = documents.receipts() if (not argv or argv[0] == "--all") else [documents.get(argv[0])]
    records = {}
    for d in docs:
        ex, _ = combine.combine(d)
        v = values_of(ex)
        records[d.doc_id] = v
        problems = validate(v, ex.items)
        if len(docs) == 1 or problems:
            print(f"{d.doc_id}  {d.file}: {'no problem' if not problems else ''}")
            for p in problems:
                print(f"  {p.severity:<7} {p.field:<14} {p.rule:<9} {p.message}")
    for later, first in duplicates(records).items():
        print(f"{later}: the same receipt as {first} (same order number, or same shop, date and total)")


if __name__ == "__main__":
    main()
