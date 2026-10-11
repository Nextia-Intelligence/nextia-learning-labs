"""The correction workflow: a reviewer corrects a value, and nothing is erased.

    python -m doc_extract.corrections load D045
    python -m doc_extract.corrections correct D045 total 405.61 --reviewer Grace --note "Total from the paper receipt the customer sent"
    python -m doc_extract.corrections history D045
    python -m doc_extract.corrections current D045

The database (REVIEW_DB, default out/review.db) has two tables. `extractions` keeps what the
pipeline extracted, with its evidence; `corrections` keeps every change a person made, with who,
when, why and the value before. Neither table is ever updated: the database refuses it. The
current value of a field is its latest correction, or the extracted value when nobody changed it.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from doc_extract import __version__, contract, provenance

SCHEMA = """
CREATE TABLE IF NOT EXISTS extractions (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL, file TEXT NOT NULL, field TEXT NOT NULL,
    value TEXT, status TEXT NOT NULL, reason TEXT, evidence TEXT,
    pipeline_version TEXT NOT NULL, contract_version TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL, field TEXT NOT NULL,
    old_value TEXT, new_value TEXT, reviewer TEXT NOT NULL, note TEXT NOT NULL,
    version INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS keep_extractions BEFORE UPDATE ON extractions
BEGIN SELECT RAISE(ABORT, 'an extraction is never changed: add a correction'); END;
CREATE TRIGGER IF NOT EXISTS keep_corrections BEFORE UPDATE ON corrections
BEGIN SELECT RAISE(ABORT, 'a correction is never changed: add a new one'); END;
"""


def connect(path: str | None = None) -> sqlite3.Connection:
    p = Path(path or os.environ.get("REVIEW_DB", "out/review.db"))
    p.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(p)
    db.executescript(SCHEMA)
    return db


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def store(db: sqlite3.Connection, doc_id: str, ex) -> int:
    """Keep one extraction (every field with its evidence). Returns the number of fields stored."""
    rec = provenance.record(ex)
    with db:
        for name, f in rec["fields"].items():
            db.execute("INSERT INTO extractions (doc_id, file, field, value, status, reason, evidence, pipeline_version,"
                       " contract_version, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (doc_id, ex.file, name, f["value"], f["status"], f["reason"], json.dumps(f["evidence"]),
                        __version__, contract.CONTRACT_VERSION, now()))
    return len(rec["fields"])


def current(db: sqlite3.Connection, doc_id: str) -> dict[str, dict]:
    """field -> {value, source}: the latest correction, else the latest extraction."""
    out: dict[str, dict] = {}
    for field, value, status in db.execute(
            "SELECT field, value, status FROM extractions WHERE doc_id = ? ORDER BY id", (doc_id,)):
        out[field] = {"value": value, "source": f"extracted ({status})"}
    for field, new, reviewer, version in db.execute(
            "SELECT field, new_value, reviewer, version FROM corrections WHERE doc_id = ? ORDER BY id", (doc_id,)):
        out[field] = {"value": new, "source": f"corrected by {reviewer} (version {version})"}
    return out


def correct(db: sqlite3.Connection, doc_id: str, field: str, new_value: str | None, reviewer: str, note: str) -> int:
    """Add a correction. The note is required: a correction without a reason cannot be checked later."""
    if field not in contract.FIELDS:
        raise ValueError(f"{field} is not a field of the contract")
    if not note.strip():
        raise ValueError("a correction needs a note that says why")
    cur = current(db, doc_id)
    if field not in cur:
        raise ValueError(f"{doc_id} has no extraction: load it first")
    version = 1 + db.execute("SELECT COUNT(*) FROM corrections WHERE doc_id = ? AND field = ?", (doc_id, field)).fetchone()[0]
    with db:
        db.execute("INSERT INTO corrections (doc_id, field, old_value, new_value, reviewer, note, version, created_at)"
                   " VALUES (?,?,?,?,?,?,?,?)", (doc_id, field, cur[field]["value"], new_value, reviewer, note, version, now()))
    return version


def history(db: sqlite3.Connection, doc_id: str) -> list[tuple]:
    rows = [("extracted", f, v, s, json.loads(e) if e else None, t) for f, v, s, e, t in db.execute(
        "SELECT field, value, status, evidence, created_at FROM extractions WHERE doc_id = ? ORDER BY id", (doc_id,))]
    rows += [("corrected", f, f"{o} -> {n}", f"by {r}, version {v}: {note}", None, t) for f, o, n, r, note, v, t in db.execute(
        "SELECT field, old_value, new_value, reviewer, note, version, created_at FROM corrections WHERE doc_id = ? ORDER BY id",
        (doc_id,))]
    return rows


def main(argv: list[str] | None = None) -> None:
    from doc_extract import combine, documents

    ap = argparse.ArgumentParser(description="Record corrections without erasing the original values.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("load").add_argument("doc")
    c = sub.add_parser("correct")
    c.add_argument("doc")
    c.add_argument("field")
    c.add_argument("value")
    c.add_argument("--reviewer", required=True)
    c.add_argument("--note", required=True)
    sub.add_parser("history").add_argument("doc")
    sub.add_parser("current").add_argument("doc")
    args = ap.parse_args(argv)
    db = connect()
    d = documents.get(args.doc)
    if args.cmd == "load":
        ex, _ = combine.combine(d)
        print(f"{d.doc_id}: stored {store(db, d.doc_id, ex)} fields from the pipeline")
    elif args.cmd == "correct":
        v = None if args.value.lower() in ("none", "absent") else args.value
        version = correct(db, d.doc_id, args.field, v, args.reviewer, args.note)
        print(f"{d.doc_id} {args.field}: correction version {version} recorded; the extracted value is kept")
    elif args.cmd == "history":
        for kind, field, value, status, ev, _when in history(db, d.doc_id):
            where = f" (page {ev['page']}, box {[round(x) for x in ev['box']]})" if ev and ev.get("box") else ""
            print(f"  {kind:<9} {field:<15} {str(value):<22} {status}{where}")
    else:
        for field, v in current(db, d.doc_id).items():
            print(f"  {field:<15} {str(v['value']):<14} {v['source']}")


if __name__ == "__main__":
    main()
