"""Combine methods: rules where they are reliable, the vision model where they are not, and a
reconciliation when both give a value.

    python -m doc_extract.combine D017       # a partner shop's receipt: the rules do not know it
    python -m doc_extract.combine D042       # a photo: rules on OCR, no model needed

The steps for one document:
  1. read each page the way its route says (text layer, or OCR on the prepared picture);
  2. apply the rules (fields.py);
  3. call the model only when the rules are not enough: a required field is missing, the shop is
     unknown, or the reading score of a required field is low;
  4. reconcile, field by field: agree -> keep the rules' value and its box; disagree -> keep both and
     send the field to review; the model alone -> keep its value only if the printed text can be
     found on the page (grounded); otherwise mark it "unverified"; both absent -> absent, with the
     model's reason when it gives one (not_printed, cut_off, unreadable).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from doc_extract import contract, fields, ocr, route, textlayer, vision
from doc_extract.fields import Extraction, Found
from doc_extract.pages import Line, Page

LOW_SCORE = 0.80
REQUIRED = [f.name for f in contract.RECEIPT if f.required]


@dataclass
class Decision:
    used_model: bool
    why: list[str] = field(default_factory=list)
    flags: dict[str, list[str]] = field(default_factory=dict)  # field -> conflict, unverified, ...
    source: dict[str, str] = field(default_factory=dict)  # field -> rules, model, both, none


def read_pages(d) -> list[Page]:
    """Every page, read the way its route says."""
    info = route.inspect(d.path)
    pages: list[Page] = []
    text_pages = [p.page for p in info.pages if p.route == "text"]
    ocr_pages = [p.page for p in info.pages if p.route == "ocr"]
    if text_pages:
        pages += textlayer.read(d.path, text_pages)
    if ocr_pages:
        pages += ocr.read(d.path, ocr_pages, prepare=True)
    return sorted(pages, key=lambda p: p.page)


def why_model(rules: Extraction) -> list[str]:
    why = []
    missing = [n for n in REQUIRED if rules.fields[n].value is None]
    if missing:
        why.append(f"required fields missing: {', '.join(missing)}")
    if rules.fields["vendor"].reason.startswith("unknown shop"):
        why.append("an unknown shop: the rules know only Larkfield's layouts")
    low = [n for n in REQUIRED if rules.fields[n].value is not None and rules.fields[n].score < LOW_SCORE]
    if low:
        why.append(f"low reading score: {', '.join(low)}")
    return why


def ground(name: str, value: str, printed: str, pages: list[Page]) -> Line | None:
    """The line on the page that shows this value, or None (the value cannot be found on the page)."""
    want = contract.normalise(name, value)
    p = (printed or "").strip().lower()
    for page in pages:
        for ln in page.lines:
            t = ln.text
            if p and len(p) >= 3 and p in t.lower():
                return ln
            if name in ("subtotal", "shipping", "tax", "total") and contract.money(t) == want:
                return ln
            if name == "date" and want in (contract.parse_date(t, True), contract.parse_date(t)):
                return ln
            if name == "order_number" and contract.order_number(t) == want:
                return ln
            if name == "payment_method" and contract.payment(t) == want:
                return ln
            if name in ("vendor", "currency") and want and want.lower() in contract.normalise("vendor", t):
                return ln
    return None


def combine(d, use_model: bool = True) -> tuple[Extraction, Decision]:
    pages = read_pages(d)
    rules = fields.extract(pages, "rules")
    why = why_model(rules)
    dec = Decision(bool(why) and use_model, why)
    out = Extraction(d.file, "combined", pages=pages, seconds=rules.seconds)
    model = vision.read(d.file, d.truth.get("receipt_page", 1)) if dec.used_model else None
    if dec.used_model and model is None:
        dec.why.append("no recorded model answer for this file: rules only")
    if model:
        out.usage = model.usage
        out.seconds += model.seconds
    for name in vision.FIELD_NAMES:
        r = rules.fields[name]
        m = model.fields.get(name) if model else None
        flags: list[str] = []
        if m is None or (r.value is None and m.value is None) or (
                r.value is not None and m.value is not None and
                contract.normalise(name, r.value) == contract.normalise(name, m.value)):
            chosen, src = r, ("both" if m is not None and r.value is not None else "rules")
            if m is not None and r.value is None and m.value is None:  # both absent: keep the model's reason
                chosen = Found(name, None, "absent", m.reason or r.reason)  # (cut_off, unreadable, ...)
                src = "none"
        elif r.value is not None and m.value is not None:  # they disagree: keep the rules' value, review
            chosen, src = r, "rules"
            flags.append(f"conflict: the rules read {r.value}, the model read {m.value}")
        elif r.value is None and m.value is not None:
            line = ground(name, m.value, m.raw, pages)
            if line is not None:
                chosen = Found(name, m.value, m.status, m.reason, m.raw, [line], line_page(line, pages), m.confidence)
            else:
                chosen = Found(name, m.value, "unverified", m.reason, m.raw, [], m.page, m.confidence)
                flags.append("unverified: the model's value cannot be found on the page")
            src = "model"
        else:  # the rules found it, the model says absent
            chosen, src = r, "rules"
            flags.append(f"the model says absent ({m.reason or 'no reason'})")
        if r.value is not None and r.score < LOW_SCORE:
            flags.append(f"low reading score {r.score:.2f}")
        out.fields[name] = chosen
        dec.source[name] = src
        if flags:
            dec.flags[name] = flags
    out.items = rules.items if rules.items or not model else model.items
    return out, dec


def line_page(line: Line, pages: list[Page]) -> int:
    return next((p.page for p in pages if any(ln is line for ln in p.lines)), 1)


def main(argv: list[str] | None = None) -> None:
    from doc_extract import compare, documents

    argv = sys.argv[1:] if argv is None else argv
    d = documents.get(argv[0] if argv else "D017")
    ex, dec = combine(d)
    print(f"{d.doc_id}  {d.file}: model {'used' if dec.used_model else 'not needed'}"
          + (f" ({'; '.join(dec.why)})" if dec.why else ""))
    for name, f in ex.fields.items():
        want = d.fields.get(name)
        mark = "ok" if compare.correct(name, f.value, want) else f"WRONG (true: {want})"
        flags = f"  [{'; '.join(dec.flags[name])}]" if name in dec.flags else ""
        shown = f.value if f.value is not None else f"({f.reason or 'absent'})"
        print(f"  {name:<15} {shown:<14} from {dec.source[name]:<5} {f.status:<10} {mark}{flags}")


if __name__ == "__main__":
    main()
