"""Check the shape of a matching pack before you hand it in. It does not know the answers and gives no score.

    python check_submission.py PACK_FOLDER [--data DATA_FOLDER]

PACK_FOLDER holds links.csv, entities.csv, golden.csv, history.jsonl, my_labels.csv and REPORT.md.
DATA_FOLDER is the course data (default: LARKFIELD_DATA, else ./data, the layout of larkfield-match).
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REVIEW_PER_DAY = 300   # Ivana's capacity, an assumption of the course (data/costs.json)
NEEDED = {
    "links.csv": ["record_id_l", "record_id_r", "score", "decision"],
    "entities.csv": ["record_id", "entity_id"],
    "golden.csv": ["entity_id"],
    "my_labels.csv": ["record_id_l", "record_id_r", "band", "my_label"],
}


def read(p):
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack")
    ap.add_argument("--data", default=os.environ.get("LARKFIELD_DATA", "data"))
    a = ap.parse_args()
    pack, data = Path(a.pack), Path(a.data)
    problems, notes = [], []

    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        if hashlib.sha256((HERE / name.strip()).read_bytes()).hexdigest() != digest:
            problems.append(f"{name.strip()} in {HERE} is changed: download the final files again")
    fh = set(read(HERE / "fernhollow_customers.csv").record_id)
    lk = set()
    for f in ("shop_accounts.csv", "loyalty_members.csv", "garden_centres.csv"):
        p = data / "sources" / f
        if not p.exists():
            sys.exit(f"No course data in {data}: run this from larkfield-match, or pass --data.")
        lk |= set(read(p).record_id)
    known = fh | lk

    files = {}
    for name, cols in NEEDED.items():
        p = pack / name
        if not p.exists():
            problems.append(f"{name} is missing")
            continue
        df = read(p)
        miss = [c for c in cols if c not in df.columns]
        if miss:
            problems.append(f"{name} has no column {', '.join(miss)}")
            continue
        files[name] = df
    for name in ("REPORT.md", "history.jsonl"):
        if not (pack / name).exists():
            problems.append(f"{name} is missing")

    if "links.csv" in files:
        ln = files["links.csv"]
        ids = set(ln.record_id_l) | set(ln.record_id_r)
        if ids - known:
            problems.append(f"links.csv: {len(ids - known)} unknown record IDs, for example {sorted(ids - known)[:3]}")
        no_fh = ~(ln.record_id_l.isin(fh) | ln.record_id_r.isin(fh))
        if no_fh.any():
            problems.append(f"links.csv: {int(no_fh.sum())} pairs have no Fernhollow record")
        if (ln.record_id_l == ln.record_id_r).any():
            problems.append("links.csv: a record paired with itself")
        key = ln[["record_id_l", "record_id_r"]].apply(lambda r: tuple(sorted(r)), axis=1)
        if key.duplicated().any():
            problems.append(f"links.csv: {int(key.duplicated().sum())} pairs appear twice")
        bad = set(ln.decision) - {"link", "review"}
        if bad:
            problems.append(f"links.csv: decision must be link or review, not {sorted(bad)[:3]}")
        try:
            pd.to_numeric(ln.score)
        except ValueError:
            problems.append("links.csv: score must be a number")
        n_link, n_rev = int((ln.decision == "link").sum()), int((ln.decision == "review").sum())
        notes.append(f"links: {n_link:,} pairs to link, {n_rev:,} pairs to review "
                     f"= {n_rev / REVIEW_PER_DAY:.1f} days for one reviewer at {REVIEW_PER_DAY} pairs a day")

    if "entities.csv" in files:
        en = files["entities.csv"]
        if en.record_id.duplicated().any():
            problems.append(f"entities.csv: {int(en.record_id.duplicated().sum())} records are in two entities")
        missing = known - set(en.record_id)
        if missing:
            problems.append(f"entities.csv: {len(missing):,} records have no entity, for example {sorted(missing)[:3]}")
        extra = set(en.record_id) - known
        if extra:
            problems.append(f"entities.csv: {len(extra)} unknown record IDs")
        size = en.groupby("entity_id").size()
        has_lk = en[en.record_id.isin(lk)].entity_id.unique()
        fh_rows = en[en.record_id.isin(fh)]
        joined = int(fh_rows.entity_id.isin(has_lk).sum())
        top = size.sort_values(ascending=False).head(3)
        notes.append(f"entities: {en.entity_id.nunique():,} customers from {len(en):,} records; "
                     f"{joined:,} of {len(fh_rows):,} Fernhollow records are in an entity with a Larkfield record")
        notes.append("largest entities: " + ", ".join(f"{e} ({n} records)" for e, n in top.items()))
        if "golden.csv" in files:
            gd = files["golden.csv"]
            if gd.entity_id.duplicated().any():
                problems.append("golden.csv: an entity has two golden records")
            nogold = set(en.entity_id) - set(gd.entity_id)
            if nogold:
                problems.append(f"golden.csv: {len(nogold):,} entities have no golden record")
            if not any(c.endswith("_from") for c in gd.columns):
                problems.append("golden.csv: no column says which record each value came from (for example name_from)")

    if "my_labels.csv" in files:
        ml = files["my_labels.csv"]
        notes.append(f"your labelled sample: {len(ml)} pairs; by band: "
                     + ", ".join(f"{b} {n}" for b, n in ml.band.value_counts().items()))
        if len(ml) < 100:
            problems.append("my_labels.csv: label at least 100 pairs")
        bad = set(ml.my_label) - {"0", "1", "unsure"}
        if bad:
            problems.append(f"my_labels.csv: my_label must be 1, 0 or unsure, not {sorted(bad)[:3]}")

    if (pack / "history.jsonl").exists():
        try:
            n = sum(1 for x in (pack / "history.jsonl").read_text().splitlines() if x.strip() and json.loads(x))
            notes.append(f"history: {n:,} events")
        except json.JSONDecodeError:
            problems.append("history.jsonl: a line is not JSON")

    for x in notes:
        print(x)
    if problems:
        print("\nNot ready yet:")
        for x in problems:
            print("  - " + x)
        sys.exit(1)
    print("\nThe pack has the right shape. This check gives no score: the reviewer grades the content.")


if __name__ == "__main__":
    main()
