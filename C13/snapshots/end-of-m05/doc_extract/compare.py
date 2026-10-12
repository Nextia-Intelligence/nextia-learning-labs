"""Compare the three paths on the same document: the PDF text layer, OCR and the vision model.

    python -m doc_extract.compare D011              # one document: every field, every path
    python -m doc_extract.compare --all             # every receipt: correct fields per path and source
    python -m doc_extract.compare D036 --prepare    # OCR on the prepared picture (prepare.py)

A field is correct when its normalised value equals the true value (both absent counts as correct).
The vision answers are the course's recordings (no key, no cost now); their cost is the cost when
they were recorded.
"""

from __future__ import annotations

import argparse

from doc_extract import contract, documents, fields, files, ocr, prices, textlayer, vision
from doc_extract.fields import Extraction

PATHS = ("text", "ocr", "vision")


def run(d: documents.Document, path: str, prepare: bool = False) -> Extraction | None:
    """One path on one document, or None when the path cannot read it."""
    if path == "text":
        if not files.is_pdf(d.path):
            return None
        return fields.extract(textlayer.read(d.path), "text")
    if path == "ocr":
        return fields.extract(ocr.read(d.path, prepare=prepare), "ocr")
    if path == "vision":
        return vision.read(d.file, d.truth.get("receipt_page", 1))
    raise ValueError(path)


def correct(name: str, got: str | None, want: str | None) -> bool:
    g, w = contract.normalise(name, got), contract.normalise(name, want)
    if name == "shipping":  # not printed counts as 0.00
        g, w = g or "0.00", w or "0.00"
    return g == w


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Compare the text layer, OCR and the vision model.")
    ap.add_argument("doc", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--prepare", action="store_true", help="prepare pictures before OCR")
    args = ap.parse_args(argv)
    if args.all or not args.doc:
        table: dict[tuple[str, str], list[int]] = {}
        for d in documents.receipts():
            for p in PATHS:
                ex = run(d, p, args.prepare)
                if ex is None:
                    continue
                ok = sum(correct(n, ex.value(n), d.fields.get(n)) for n in vision.FIELD_NAMES)
                cell = table.setdefault((d.source, p), [0, 0, 0])
                cell[0] += ok
                cell[1] += len(vision.FIELD_NAMES)
                cell[2] += 1
        print(f"{'source':<12}" + "".join(f"{p:>20}" for p in PATHS))
        for src in ("digital_pdf", "scan_pdf", "scan_image", "photo", "mixed_pdf"):
            cells = []
            for p in PATHS:
                c = table.get((src, p))
                cells.append(f"{c[0]}/{c[1]} ({c[0] / c[1]:.0%})" if c else "cannot read")
            print(f"{src:<12}" + "".join(f"{c:>20}" for c in cells))
        print("Correct fields of 9 per receipt; a field is correct when its normalised value is the true one.")
        return
    d = documents.get(args.doc)
    results = {p: run(d, p, args.prepare) for p in PATHS}
    print(f"{d.doc_id}  {d.file}  ({d.source}, {d.language})")
    print(f"{'field':<15} {'true value':<14}" + "".join(f"{p:<16}" for p in PATHS))
    for n in vision.FIELD_NAMES:
        want = d.fields.get(n)
        row = f"{n:<15} {str(want if want is not None else '-'):<14}"
        for p in PATHS:
            ex = results[p]
            if ex is None:
                row += f"{'(cannot read)':<16}"
                continue
            got = ex.value(n)
            mark = "ok" if correct(n, got, want) else "WRONG"
            row += f"{(str(got if got is not None else '-')[:10] + ' ' + mark):<16}"
        print(row)
    print()
    for p, ex in results.items():
        if ex is None:
            continue
        ok = sum(correct(n, ex.value(n), d.fields.get(n)) for n in vision.FIELD_NAMES)
        extra = ""
        if p == "vision" and ex.usage.get("tokens_in"):
            extra = f", {ex.usage['tokens_in']} + {ex.usage['tokens_out']} tokens = US${prices.cost(ex.usage['tokens_in'], ex.usage['tokens_out']):.4f} (recorded)"
        print(f"{p:<7} {ok}/9 correct, {ex.seconds:.2f} s{extra}")


if __name__ == "__main__":
    main()
