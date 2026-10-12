"""The whole pipeline, with versions, reprocessing, deletion and a regression set.

    python -m doc_extract.pipeline run                 # every document: intake, read, extract, validate, review
    python -m doc_extract.pipeline run --only D045
    python -m doc_extract.pipeline status              # which stored results were made by an older version
    python -m doc_extract.pipeline reprocess           # run again only those
    python -m doc_extract.pipeline delete D045         # delete everything the pipeline made from one document
    python -m doc_extract.pipeline regression          # compare with tests/regression/expected.json

One result per document in out/results/<doc_id>.json: the intake decision, every field with its
status and evidence, the validation problems, the review decision, and the versions that made it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from doc_extract import __version__, combine, contract, documents, intake, ocr, provenance, review, validate

RESULTS = Path("out/results")
REGRESSION = Path(__file__).resolve().parents[1] / "tests" / "regression" / "expected.json"
REGRESSION_SET = ["D001", "D004", "D017", "D021", "D025", "D036", "D045", "D046", "D047", "D049", "D050", "D058", "D059",
                  "D061", "D064"]


def versions() -> dict:
    return {"pipeline": __version__, "contract": contract.CONTRACT_VERSION,
            "ocr": f"{ocr.engine_name()}, {ocr.OCR_DPI} dpi, max side {ocr.MAX_SIDE}",
            "vision": "recorded chat-strong, prompt v2"}


def process(d, registry: intake.Registry) -> dict:
    res = {"doc_id": d.doc_id, "file": d.file, "versions": versions(),
           "processed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    check = intake.check(d.path, registry)
    res["intake"] = {"status": check.status, "reason": check.reason, "sha256": check.sha256}
    if not check.accepted:
        res["review"] = {"needed": check.status not in ("duplicate",), "reasons": [f"intake: {check.status}: {check.reason}"]}
        return res
    if d.kind in ("policy", "price_list", "spreadsheet"):
        res["review"] = {"needed": False, "reasons": ["not a receipt: read with sections.py, tables.py or sheets.py"]}
        return res
    ex, dec = combine.combine(d)
    rec = provenance.record(ex)
    res["fields"] = rec["fields"]
    res["model_used"] = dec.used_model
    res["model_why"] = dec.why
    res["flags"] = dec.flags
    res["usage"] = ex.usage if dec.used_model else {}
    problems = validate.validate(validate.values_of(ex), ex.items)
    res["validation"] = [p.__dict__ for p in problems]
    reasons = [f"{p.field}: {p.message}" for p in problems if p.severity == "error"]
    reasons += [f"{n}: {x}" for n, fl in dec.flags.items() for x in fl if x.startswith(("conflict", "unverified"))]
    cert = review.certainty(ex, dec)
    res["certainty"] = cert
    needed = bool(reasons) or cert < review.DEFAULT_THRESHOLD
    if not reasons and needed:
        reasons = [f"certainty {cert:.2f} is under {review.DEFAULT_THRESHOLD}"]
    res["review"] = {"needed": needed, "reasons": reasons}
    return res


def save(res: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / f"{res['doc_id']}.json"
    p.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return p


def run(only: list[str] | None = None) -> list[dict]:
    registry = intake.Registry()
    out = []
    for d in documents.load():  # in the order they arrived: the registry needs the earlier files
        if only and d.doc_id not in only:
            intake.check(d.path, registry)
            continue
        res = process(d, registry)
        save(res)
        out.append(res)
    dup = validate.duplicates({r["doc_id"]: {k: v["value"] for k, v in r.get("fields", {}).items()} for r in out})
    for later, first in dup.items():
        r = next(x for x in out if x["doc_id"] == later)
        r["review"]["needed"] = True
        r["review"]["reasons"].append(f"possible duplicate of {first}: same order number, or same shop, date and total")
        save(r)
    return out


def stale() -> list[str]:
    now = versions()
    out = []
    for p in sorted(RESULTS.glob("D*.json")):
        if json.loads(p.read_text(encoding="utf-8")).get("versions") != now:
            out.append(p.stem)
    return out


def delete(doc_id: str) -> list[str]:
    """Delete the derived data of one document: its result, its OCR cache, its review rows. Writes
    one line to out/deletions.log (what and when, not the content)."""
    d = documents.get(doc_id)
    removed = []
    r = RESULTS / f"{d.doc_id}.json"
    if r.exists():
        r.unlink()
        removed.append(str(r))
    if d.path.exists():
        prefix = hashlib.sha256(d.path.read_bytes()).hexdigest()[:16]
        for c in ocr.CACHE.glob(f"{prefix}-*.json"):
            c.unlink()
            removed.append(str(c))
    db_path = Path(os.environ.get("REVIEW_DB", "out/review.db"))
    if db_path.exists():
        from doc_extract import corrections

        db = corrections.connect(str(db_path))
        with db:
            n1 = db.execute("DELETE FROM extractions WHERE doc_id = ?", (d.doc_id,)).rowcount
            n2 = db.execute("DELETE FROM corrections WHERE doc_id = ?", (d.doc_id,)).rowcount
        if n1 or n2:
            removed.append(f"{db_path}: {n1} extraction rows, {n2} correction rows")
    log = Path("out/deletions.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"doc_id": d.doc_id, "deleted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "removed": len(removed)}) + "\n")
    return removed


def snapshot(res: dict) -> dict:
    """The part of a result that must not change without a reason: intake, values, statuses, review."""
    return {"intake": res["intake"]["status"],
            "fields": {k: [v["value"], v["status"]] for k, v in res.get("fields", {}).items()},
            "review": res["review"]["needed"]}


def regression(update: bool = False) -> list[str]:
    results = {r["doc_id"]: snapshot(r) for r in run() if r["doc_id"] in REGRESSION_SET}
    if update:
        REGRESSION.parent.mkdir(parents=True, exist_ok=True)
        REGRESSION.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return []
    expected = json.loads(REGRESSION.read_text(encoding="utf-8"))
    diffs = []
    for doc_id, want in expected.items():
        got = results.get(doc_id)
        if got != want:
            for k in ("intake", "review"):
                if got[k] != want[k]:
                    diffs.append(f"{doc_id} {k}: expected {want[k]}, got {got[k]}")
            for f, v in want["fields"].items():
                if got["fields"].get(f) != v:
                    diffs.append(f"{doc_id} {f}: expected {v}, got {got['fields'].get(f)}")
    return diffs


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Run the whole pipeline.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--only", default="")
    sub.add_parser("status")
    sub.add_parser("reprocess")
    sub.add_parser("delete").add_argument("doc")
    g = sub.add_parser("regression")
    g.add_argument("--update", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
        out = run(only)
        counts: dict[str, int] = {}
        for res in out:
            key = "stopped at intake" if res["intake"]["status"] not in ("accepted", "wrong_extension") else (
                "to review" if res["review"]["needed"] else "straight to the agents")
            counts[key] = counts.get(key, 0) + 1
            if only:
                print(json.dumps(res, indent=1, ensure_ascii=False)[:3000])
        print(f"{len(out)} documents: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
        print(f"results in {RESULTS}/")
    elif args.cmd == "status":
        old = stale()
        print(f"{len(list(RESULTS.glob('D*.json')))} results; {len(old)} made by an older version: {', '.join(old) or '-'}")
        print(f"current versions: {versions()}")
    elif args.cmd == "reprocess":
        old = stale()
        if old:
            run(old)
        print(f"reprocessed {len(old)} documents")
    elif args.cmd == "delete":
        for x in delete(args.doc) or ["nothing to delete"]:
            print(f"  removed {x}")
        print("The original file belongs to the ticket system: delete it there (this pipeline never changes it).")
    elif args.cmd == "regression":
        diffs = regression(args.update)
        if args.update:
            print(f"wrote {REGRESSION}")
        else:
            print("\n".join(diffs) if diffs else f"regression set: {len(REGRESSION_SET)} documents, no change")
            if diffs:
                raise SystemExit(1)


if __name__ == "__main__":
    main()
