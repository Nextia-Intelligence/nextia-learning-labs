"""Make one data folder for the final assignment: the course data plus the Home office launch.

Run it in your larkfield-recs folder, with the course data in data/ (as in Meet the shop log):

    python ../nextia-learning-labs/C37/final/make_data.py
    python ../nextia-learning-labs/C37/final/make_data.py --validation 2026-06-22 2026-07-05 --test 2026-07-27 2026-08-02

It writes final-data/ (your data/ folder does not change). Give it to the `recs` command with
LARKFIELD_DATA=final-data, and keep its outputs apart with LARKFIELD_OUTPUTS=outputs-final.

The periods of final-data/splits.json:
  launch      2026-07-20 .. 2026-08-02   the first two weeks of Home office (train on everything before its launch)
  validation  your choice (default 2026-06-22 .. 07-05, the course's test period)   for tuning
  test        your choice (default 2026-07-27 .. 08-02)   use it once, to report
Your periods must end on or before 2026-08-02: the files stop there. The course team keeps the weeks after it.
The data is synthetic: the course's code made it with a model of customer behaviour.
"""

import argparse
import gzip
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LAUNCH = ("2026-07-20", "2026-08-02")
LAST_DAY = "2026-08-02"
GAP = ("2026-07-06", "2026-07-19")
DEFAULT_VALIDATION = ("2026-06-22", "2026-07-05")
DEFAULT_TEST = ("2026-07-27", "2026-08-02")
# popular on the default validation period, quick sample: the value `recs check` compares with
EXPECTED_DEFAULT = 0.1057


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_sums(folder):
    bad = []
    for line in (folder / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            p = folder / name.strip()
            if not p.exists() or sha(p) != digest:
                bad.append(name.strip())
    return bad


def period(arg, name):
    first, last = arg
    try:
        a, b = date.fromisoformat(first), date.fromisoformat(last)
    except ValueError:
        raise SystemExit(f"--{name}: write the days as YYYY-MM-DD, for example 2026-07-20 2026-07-26")
    if b < a:
        raise SystemExit(f"--{name}: the last day {last} is before the first day {first}")
    if b > date.fromisoformat(LAST_DAY):
        raise SystemExit(f"--{name}: the files stop on {LAST_DAY}. The weeks after it are graded: they are not "
                         "in the files, and no period can use them.")
    if a <= date.fromisoformat(GAP[1]) and b >= date.fromisoformat(GAP[0]):
        raise SystemExit(f"--{name}: {GAP[0]} to {GAP[1]} has no events in the files. Choose days outside it.")
    return [first, last]


def main():
    ap = argparse.ArgumentParser(description="Make final-data/: the course data plus the Home office launch.")
    ap.add_argument("--course-data", default="data", help="the course data folder (default data)")
    ap.add_argument("--out", default="final-data", help="the folder to write (default final-data)")
    ap.add_argument("--validation", nargs=2, metavar=("FIRST", "LAST"), default=list(DEFAULT_VALIDATION))
    ap.add_argument("--test", nargs=2, metavar=("FIRST", "LAST"), default=list(DEFAULT_TEST))
    a = ap.parse_args()
    val, test = period(a.validation, "validation"), period(a.test, "test")
    if test[0] <= val[1]:
        print(f"Note: your test period starts on or before the end of your validation period ({val[1]}). "
              "Tuning on one and reporting on the other is then not a clean test.")

    course, out = Path(a.course_data), Path(a.out)
    if not (course / "events.csv.gz").exists():
        raise SystemExit(f"No course data in {course}/. Run this in your larkfield-recs folder, or give "
                         "--course-data with the path of the course's data folder.")
    for folder, what in ((course, "course data"), (HERE, "final folder")):
        bad = check_sums(folder)
        if bad:
            raise SystemExit(f"These files of the {what} are missing or changed: {', '.join(bad)}. "
                             "Get them again (git pull in nextia-learning-labs).")
    if out.resolve() == course.resolve():
        raise SystemExit("--out must be a new folder, not the course data folder.")

    products = pd.read_csv(course / "products.csv", keep_default_na=False, na_values=[])
    new_products = pd.read_csv(HERE / "products_new.csv", keep_default_na=False, na_values=[])
    customers = pd.read_csv(course / "customers.csv", keep_default_na=False, na_values=[])
    new_customers = pd.read_csv(HERE / "customers_new.csv", keep_default_na=False, na_values=[])
    events = pd.read_csv(course / "events.csv.gz", keep_default_na=False, na_values=[""])
    new_events = pd.read_csv(HERE / "events_final.csv.gz", keep_default_na=False, na_values=[""])
    emb = np.load(course / "embeddings" / "products.npy")
    emb_new = np.load(HERE / "embeddings" / "products_new.npy")
    if len(emb) != len(products) or len(emb_new) != len(new_products):
        raise SystemExit("The embeddings do not match the products. Get the files again.")

    if out.exists():
        shutil.rmtree(out)
    (out / "embeddings").mkdir(parents=True)
    pd.concat([products, new_products], ignore_index=True).to_csv(out / "products.csv", index=False)
    pd.concat([customers, new_customers], ignore_index=True).to_csv(out / "customers.csv", index=False)
    all_events = pd.concat([events, new_events], ignore_index=True)
    with gzip.open(out / "events.csv.gz", "wt", encoding="utf-8", compresslevel=6) as f:
        all_events.to_csv(f, index=False)
    np.save(out / "embeddings" / "products.npy", np.vstack([emb, emb_new]).astype(np.float16))
    model = json.loads((course / "embeddings" / "model.json").read_text())
    model["products"] = len(products) + len(new_products)
    model["note"] = "rows in products.csv order: the course's products, then the 150 Home office products"
    (out / "embeddings" / "model.json").write_text(json.dumps(model, indent=2) + "\n")
    shutil.copy2(course / "costs.json", out / "costs.json")

    splits = json.loads((course / "splits.json").read_text())
    splits.update({
        "launch": list(LAUNCH), "validation": val, "test": test,
        "course_validation": splits["validation"], "course_test": splits["test"],
        "missing": list(GAP), "last_day": LAST_DAY,
        "note": "Final assignment. Train on everything before a period's first day; predict the orders of the "
                "period. 'launch' = the first two weeks of Home office (launched on 2026-07-20), trained on the "
                "events before the launch. 2026-07-06 to 2026-07-19 is missing from the files. The files stop on "
                "2026-08-02; the course team grades on the weeks after it."})
    (out / "splits.json").write_text(json.dumps(splits, indent=2) + "\n")
    default = (val == list(DEFAULT_VALIDATION))
    (out / "expected.json").write_text(json.dumps({
        "popular_validation_quick_recall10": EXPECTED_DEFAULT if default else None,
        "note": "recs check compares popular on the validation period (quick sample) with this value; "
                "it is known only for the default validation period"}, indent=2) + "\n")

    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    (out / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(out).as_posix()}\n" for p in files))

    n_new_c = int(new_events.customer_id.isin(set(new_customers.customer_id)).groupby(new_events.customer_id).any().sum())
    print(f"Wrote {out}/: {len(products) + len(new_products):,} products ({len(new_products)} new in Home office), "
          f"{len(customers) + len(new_customers):,} customers ({len(new_customers):,} new, {n_new_c:,} of them "
          f"with events), {len(all_events):,} events to {LAST_DAY}")
    print(f"Periods: launch {LAUNCH[0]} to {LAUNCH[1]}, validation {val[0]} to {val[1]}, test {test[0]} to {test[1]}")
    print(f"No events from {GAP[0]} to {GAP[1]}; the files stop on {LAST_DAY}.")
    if not default:
        print("Note: recs check knows the expected value only for the default validation period. Use recs info.")


if __name__ == "__main__":
    sys.exit(main())
