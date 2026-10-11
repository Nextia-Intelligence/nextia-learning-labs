"""Confidence and review routing: which documents a person must check, and why.

    python -m doc_extract.review                     # the review queue at the default threshold
    python -m doc_extract.review --threshold 0.95    # another threshold
    python -m doc_extract.review --sweep             # review rate and wrong totals for many thresholds
    python -m doc_extract.review --calibration       # is the model's own confidence right?

A document goes to review when:
  - a validation error remains (validate.py), or a required field is missing;
  - a field has a conflict or an unverified model value (combine.py);
  - its certainty is under the threshold. Certainty is a number we can measure: the lowest
    reading score of the required fields' evidence (OCR scores; 1.0 for the PDF text layer).
    A value that only the model gave has no reading score: its certainty is 0.5.
The model's own "confidence" is NOT used: --calibration shows why.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from doc_extract import combine, compare, documents, validate, vision

DEFAULT_THRESHOLD = 0.90
QUEUE = Path("out/review-queue.json")


@dataclass
class Routed:
    doc_id: str
    file: str
    certainty: float
    reasons: list[str] = field(default_factory=list)

    def needs_review(self, threshold: float) -> bool:
        return bool(self.reasons) or self.certainty < threshold


def certainty(ex, dec) -> float:
    vals = []
    for name in combine.REQUIRED:
        f = ex.fields[name]
        if f.value is None:
            continue
        vals.append(f.score if dec.source.get(name) in ("rules", "both") else 0.5)
    return round(min(vals), 4) if vals else 0.0


def route_doc(d) -> tuple[Routed, object]:
    ex, dec = combine.combine(d)
    problems = [p for p in validate.validate(validate.values_of(ex), ex.items) if p.severity == "error"]
    reasons = [f"{p.field}: {p.message}" for p in problems]
    for name, flags in dec.flags.items():
        reasons += [f"{name}: {x}" for x in flags if x.startswith(("conflict", "unverified"))]
    return Routed(d.doc_id, d.file, certainty(ex, dec), reasons), ex


def outcomes(threshold: float, routed: list[tuple[Routed, object, documents.Document]]) -> dict:
    """What happens at one threshold: how many documents a person checks, and how many wrong
    totals go straight to the agents."""
    reviewed = wrong_total_auto = wrong_total_caught = wrong_any_auto = 0
    for r, ex, d in routed:
        rev = r.needs_review(threshold)
        reviewed += rev
        total_ok = compare.correct("total", ex.value("total"), d.fields.get("total"))
        all_ok = all(compare.correct(n, ex.value(n), d.fields.get(n)) for n in vision.FIELD_NAMES)
        if not total_ok:
            if rev:
                wrong_total_caught += 1
            else:
                wrong_total_auto += 1
        if not all_ok and not rev:
            wrong_any_auto += 1
    n = len(routed)
    return {"threshold": threshold, "documents": n, "reviewed": reviewed, "review_rate": round(reviewed / n, 3),
            "wrong_total_caught": wrong_total_caught, "wrong_total_to_agents": wrong_total_auto,
            "wrong_field_docs_to_agents": wrong_any_auto}


def calibration(prompt: str = "v2") -> list[dict]:
    """Group the model's field answers by the confidence it gave, and count how many were right."""
    bins = [(1.0, 1.01, "1.0"), (0.95, 1.0, "0.95-0.99"), (0.8, 0.95, "0.80-0.94"), (0.0, 0.8, "under 0.80")]
    out = {label: [0, 0] for _, _, label in bins}
    for d in documents.receipts():
        ex = vision.read(d.file, d.truth.get("receipt_page", 1), prompt)
        if ex is None:
            continue
        for name, f in ex.fields.items():
            if f.confidence is None:
                continue
            ok = compare.correct(name, f.value, d.fields.get(name))
            for lo, hi, label in bins:
                if lo <= f.confidence < hi:
                    out[label][0] += 1
                    out[label][1] += ok
                    break
    return [{"confidence": k, "answers": n, "correct": c, "accuracy": round(c / n, 3) if n else None}
            for k, (n, c) in out.items()]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Decide which documents a person must check.")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--calibration", action="store_true")
    args = ap.parse_args(argv)
    if args.calibration:
        print("The model's own confidence (vision path, prompt v2) against the true values:")
        for row in calibration():
            acc = f"{row['accuracy']:.1%}" if row["accuracy"] is not None else "-"
            print(f"  confidence {row['confidence']:<11} {row['answers']:>4} answers, {row['correct']:>4} correct ({acc})")
        return
    routed = []
    for d in documents.receipts():
        r, ex = route_doc(d)
        routed.append((r, ex, d))
    if args.sweep:
        print(f"{'threshold':>9} {'reviewed':>9} {'wrong totals caught':>20} {'wrong totals to agents':>23}")
        for t in (0.0, 0.5, 0.8, 0.9, 0.95, 0.97, 0.99, 1.0):
            o = outcomes(t, routed)
            print(f"{t:>9.2f} {o['reviewed']:>4} ({o['review_rate']:.0%}) {o['wrong_total_caught']:>20} {o['wrong_total_to_agents']:>23}")
        return
    queue = []
    for r, ex, _d in routed:
        if r.needs_review(args.threshold):
            why = r.reasons or [f"certainty {r.certainty:.2f} is under {args.threshold}"]
            queue.append({"doc_id": r.doc_id, "file": r.file, "certainty": r.certainty, "reasons": why,
                          "values": {n: f.value for n, f in ex.fields.items()}})
            print(f"{r.doc_id}  {r.file:<30} {'; '.join(why)[:120]}")
    o = outcomes(args.threshold, routed)
    print(f"{o['reviewed']} of {o['documents']} documents to review ({o['review_rate']:.0%}); "
          f"wrong totals caught {o['wrong_total_caught']}, wrong totals sent to agents {o['wrong_total_to_agents']}")
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"queue written to {QUEUE}")


if __name__ == "__main__":
    main()
