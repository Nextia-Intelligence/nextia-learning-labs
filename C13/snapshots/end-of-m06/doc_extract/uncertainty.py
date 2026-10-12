"""Visual uncertainty: decide what the pipeline can say about a page before it trusts any value.

    python -m doc_extract.uncertainty D047      # a photo whose top is cut off
    python -m doc_extract.uncertainty --all     # every receipt: the signals in one table

Signals (all measurable, none of them is the model's opinion of itself):
  unreadable      OCR found almost no text, or its scores are low
  low_resolution  the text on the picture is only a few pixels high
  conflict        two pages of the same file show different values for one field
  unverified      the model gave a value that cannot be found on the page (a guess or a deduction)
  model_absent    the model said a value is absent; its reason is kept (cut_off, unreadable, ...)
  wrong_reason    an absent value whose reason the contract does not allow for that field (a receipt
                  always prints its shop and date: they can be cut_off or unreadable, never not_printed)
"""

from __future__ import annotations

import statistics
import sys
from dataclasses import dataclass, field

from doc_extract import contract, fields
from doc_extract.pages import Page

MIN_CHARS = 40
MIN_MEAN_SCORE = 0.75
MIN_TEXT_PX = 14


@dataclass
class Signals:
    file: str
    chars: int
    mean_score: float
    text_px: float  # median line height on OCR pages (0 for the text layer)
    flags: list[str] = field(default_factory=list)


def page_signals(pages: list[Page]) -> Signals:
    lines = [ln for p in pages for ln in p.lines]
    chars = sum(len(ln.text) for ln in lines)
    mean = statistics.fmean(ln.score for ln in lines) if lines else 0.0
    ocr_lines = [ln for p in pages if p.path == "ocr" for ln in p.lines]
    px = statistics.median(ln.height for ln in ocr_lines) if ocr_lines else 0.0
    s = Signals(pages[0].file if pages else "", chars, round(mean, 3), round(px, 1))
    if chars < MIN_CHARS or (lines and mean < MIN_MEAN_SCORE):
        s.flags.append(f"unreadable: {chars} characters found, mean score {mean:.2f}")
    elif ocr_lines and px < MIN_TEXT_PX:
        s.flags.append(f"low_resolution: text is about {px:.0f} pixels high")
    return s


def conflicts(pages: list[Page]) -> list[str]:
    """Fields that different pages of one file show with different values."""
    if len(pages) < 2:
        return []
    per_page = {p.page: fields.extract([p], "rules") for p in pages}
    out = []
    for name in ("order_number", "date", "total"):
        values = {pg: ex.value(name) for pg, ex in per_page.items() if ex.value(name)}
        if len({contract.normalise(name, v) for v in values.values()}) > 1:
            out.append(f"conflict: {name} differs between pages: " + ", ".join(f"page {pg} {v}" for pg, v in values.items()))
    return out


def field_signals(ex) -> list[str]:
    """Absent values with a reason worth a person's look: the picture lost them, or the reason given
    is one the extraction contract does not allow for that field."""
    out = []
    for name, f in ex.fields.items():
        if f.value is not None or f.reason in ("not_found", ""):  # found, or the rules simply did not see it
            continue
        allowed = contract.FIELDS[name].may_be_missing
        if f.reason not in allowed:
            out.append(f"{name}: absent ({f.reason}), but the contract allows only: {', '.join(allowed)}")
        elif f.reason != "not_printed":
            out.append(f"{name}: absent ({f.reason})")
    return out


def main(argv: list[str] | None = None) -> None:
    from doc_extract import combine, documents

    argv = sys.argv[1:] if argv is None else argv
    docs = documents.receipts() if (not argv or argv[0] == "--all") else [documents.get(argv[0])]
    for d in docs:
        ex, dec = combine.combine(d)
        s = page_signals(ex.pages)
        s.flags += conflicts(ex.pages)
        for name, fl in dec.flags.items():
            s.flags += [f"{name}: {x}" for x in fl if x.startswith(("unverified", "conflict"))]
        s.flags += field_signals(ex)
        if len(docs) == 1:
            print(f"{d.doc_id}  {d.file}: {s.chars} characters, mean score {s.mean_score}, text about {s.text_px} px high")
            for fl in s.flags or ["no uncertainty signal"]:
                print(f"  {fl}")
            for name, f in ex.fields.items():
                shown = f.value if f.value is not None else f"({f.reason or 'absent'})"
                print(f"  {name:<15} {shown:<14} {f.status}")
        else:
            print(f"{d.doc_id}  {d.source:<11} {s.mean_score:>5}  {'; '.join(s.flags)[:110]}")


if __name__ == "__main__":
    main()
