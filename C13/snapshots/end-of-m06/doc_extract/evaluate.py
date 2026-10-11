"""Field-level evaluation: measure every path field by field and document type by document type.

    python -m doc_extract.evaluate                      # the course pipeline (combined)
    python -m doc_extract.evaluate --systems text,ocr,ocr_prepared,vision,vision_v1,combined
    python -m doc_extract.evaluate --json out/evaluation.json

For every field of every receipt, one outcome:
  correct          the normalised value is the true value (exact: also written exactly the same way)
  correct_absent   the field is not on the document, and the system says so
  missing          the document shows a value, the system gives none
  wrong            the system gives another value
  invented         the document does not show the field, but the system gives a value
Shipping is left out of "invented": a till receipt has no shipping line, and 0.00 is not a guess.
A document is complete when every required field is correct and nothing is invented.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from doc_extract import combine, compare, contract, documents, fields, files, ocr, textlayer, vision

SYSTEMS = ("text", "ocr", "ocr_prepared", "vision", "vision_v1", "combined")
SOURCES = ("digital_pdf", "scan_pdf", "scan_image", "photo", "mixed_pdf")


def run(system: str, d) -> fields.Extraction | None:
    if system == "text":
        return fields.extract(textlayer.read(d.path), "text") if files.is_pdf(d.path) else None
    if system in ("ocr", "ocr_prepared"):
        return fields.extract(ocr.read(d.path, prepare=system == "ocr_prepared"), system)
    if system in ("vision", "vision_v1"):
        return vision.read(d.file, d.truth.get("receipt_page", 1), "v2" if system == "vision" else "v1")
    if system == "combined":
        return combine.combine(d)[0]
    raise ValueError(system)


def outcome(name: str, got: str | None, want: str | None) -> str:
    if want is None:
        return "correct_absent" if (got is None or name == "shipping") else "invented"
    if got is None:
        return "missing"
    return "correct" if compare.correct(name, got, want) else "wrong"


def evaluate(systems=("combined",), docs=None) -> dict:
    docs = docs or documents.receipts()
    out: dict = {"documents": len(docs), "systems": {}}
    for s in systems:
        cells: dict = defaultdict(lambda: defaultdict(int))
        exact: dict = defaultdict(lambda: [0, 0])
        complete: dict = defaultdict(lambda: [0, 0])
        per_doc = {}
        items_ok = items_all = 0
        for d in docs:
            ex = run(s, d)
            ok_required, invented = True, False
            row = {}
            for spec in contract.RECEIPT:
                name = spec.name
                got = ex.value(name) if ex else None
                want = d.fields.get(name)
                o = outcome(name, got, want)
                row[name] = o
                cells[(d.source, name)][o] += 1
                cells[("all", name)][o] += 1
                if want is not None:
                    exact[name][1] += 1
                    exact[name][0] += str(got).strip() == str(want)
                if spec.required and o not in ("correct", "correct_absent"):
                    ok_required = False
                invented = invented or o == "invented"
            done = ok_required and not invented
            complete[d.source][1] += 1
            complete[d.source][0] += done
            complete["all"][1] += 1
            complete["all"][0] += done
            per_doc[d.doc_id] = {"source": d.source, "complete": done, "fields": row, "read": ex is not None}
            want_items = d.truth.get("items", [])
            got_items = ex.items if ex else []
            items_all += len(want_items)
            for w in want_items:
                items_ok += any(contract.money(str(g.get("line_total"))) == w["line_total"] and
                                str(g.get("quantity")) == str(w["quantity"]) for g in got_items)
        out["systems"][s] = {
            "cells": {f"{src}|{name}": dict(v) for (src, name), v in cells.items()},
            "exact": {k: {"exact": v[0], "present": v[1]} for k, v in exact.items()},
            "complete": {k: {"complete": v[0], "documents": v[1]} for k, v in complete.items()},
            "items": {"found": items_ok, "true": items_all},
            "per_doc": per_doc,
        }
    return out


def summary(result: dict, system: str) -> dict:
    """Totals over all fields: correct, missing, wrong, invented (present = fields the documents show)."""
    tot: dict = defaultdict(int)
    for key, v in result["systems"][system]["cells"].items():
        if key.startswith("all|"):
            for k, n in v.items():
                tot[k] += n
    present = tot["correct"] + tot["missing"] + tot["wrong"]
    return dict(tot) | {"present": present, "accuracy_present": round(tot["correct"] / present, 4) if present else None}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Evaluate the paths field by field.")
    ap.add_argument("--systems", default="combined")
    ap.add_argument("--json", help="also write the full result to this file")
    args = ap.parse_args(argv)
    systems = [s.strip() for s in args.systems.split(",")]
    result = evaluate(systems)
    for s in systems:
        r = result["systems"][s]
        sm = summary(result, s)
        print(f"== {s}: {sm['correct']} of {sm['present']} printed values correct ({sm['accuracy_present']:.1%}); "
              f"missing {sm.get('missing', 0)}, wrong {sm.get('wrong', 0)}, invented {sm.get('invented', 0)}")
        print(f"{'field':<15}" + "".join(f"{src[:11]:>12}" for src in SOURCES) + f"{'exact':>8}")
        for spec in contract.RECEIPT:
            row = f"{spec.name:<15}"
            for src in SOURCES:
                c = r["cells"].get(f"{src}|{spec.name}", {})
                pres = c.get("correct", 0) + c.get("missing", 0) + c.get("wrong", 0)
                inv = c.get("invented", 0)
                cell = f"{c.get('correct', 0)}/{pres}" if pres else "-"
                row += f"{cell + ('+' + str(inv) + 'i' if inv else ''):>12}"
            e = r["exact"].get(spec.name, {"exact": 0, "present": 0})
            row += f"{e['exact']:>4}/{e['present']:<3}"
            print(row)
        comp = r["complete"]
        print("complete documents: " + ", ".join(f"{k} {v['complete']}/{v['documents']}" for k, v in comp.items()))
        print(f"item lines found: {r['items']['found']} of {r['items']['true']}  (i = invented values)")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"written to {args.json}")


if __name__ == "__main__":
    main()
