"""Turn the final assignment's data into two runs that the `xp` commands can read.

Run it in your larkfield-experiments folder (snapshot end-of-m08), with the virtual environment active:

    python ../nextia-learning-labs/C40/final-assignment/make_runs.py --primary revenue --guardrails return_rate

It checks every file against SHA256SUMS, then writes:
- runs/final-test/: the randomised test (tables customers, visits and targets). Use it with xp srm, xp analyse,
  xp weekly, xp peek, xp power --from-run and xp report. Its customers table has one more column, segment
  (device and new or returning, e.g. mobile-new), for xp analyse --by segment.
- runs/final-soft/: the soft launch (table customers). The column used_block is a copy of turned_on_new_look,
  the name that xp adjust and xp refute read.

--primary and --guardrails come from your test plan: xp report uses them. Write the plan first.
The data files do not change. There is no truth.json with the true effects: xp check cannot help here.
"""

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
NOTE = ("The course team keeps the true effects of the final assignment. Your reviewer compares your answers "
        "with them: xp check cannot.")


def check_files(data: Path):
    bad = []
    for line in (data / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        path = data / name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            bad.append(name)
    if bad:
        raise SystemExit(f"These files are missing or changed: {', '.join(bad)}. Pull the labs repository again.")


def write_run(folder: Path, tables: dict, meta: dict):
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    files = {}
    for name, df in tables.items():
        fname = f"{name}.csv.gz" if len(df) > 50_000 else f"{name}.csv"
        df.to_csv(folder / fname, index=False,
                  compression={"method": "gzip", "mtime": 0} if fname.endswith(".gz") else None)
        files[name] = {"file": fname, "rows": len(df)}
    meta = {**meta, "tables": files, "data": "Synthetic: made by the course simulator. There are no real people."}
    (folder / "scenario.json").write_text(json.dumps(meta, indent=2) + "\n")
    (folder / "truth.json").write_text(json.dumps({"planted": NOTE}, indent=2) + "\n")
    return files


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=str(HERE / "data"), help="the folder with the data files")
    p.add_argument("--primary", required=True, help="the primary metric of your plan, e.g. revenue")
    p.add_argument("--guardrails", default="", help="comma-separated guardrail metrics of your plan")
    args = p.parse_args()
    data = Path(args.data)
    check_files(data)
    about = json.loads((data / "scenario.json").read_text())
    runs = Path(os.environ.get("LARKFIELD_RUNS", "runs"))
    customers = pd.read_csv(data / "test_customers.csv.gz")
    # xp analyse --by takes one column: segment joins device and new or returning.
    customers["segment"] = customers["device"] + customers["new_customer"].map({1: "-new", 0: "-returning"})
    for metric in [args.primary] + [g for g in args.guardrails.split(",") if g]:
        if metric not in customers.columns and metric not in ("converted", "return_rate", "order_value"):
            raise SystemExit(f"No metric '{metric}' in the test. Use converted, return_rate, order_value or a "
                             f"column: {', '.join(customers.columns)}.")
    t = about["test"]
    end = (pd.Timestamp(t["start"]) + pd.Timedelta(days=t["days"] - 1)).date().isoformat()
    test = write_run(runs / "final-test", {
        "customers": customers,
        "visits": pd.read_csv(data / "test_visits.csv.gz"),
        "targets": pd.read_csv(data / "next_month_customers.csv"),
    }, {"scenario": "final-test", "about": "the 'complete the look' block: an A/B test by customer, 28 days",
        "unit": "customer", "split": t["split"], "start": t["start"], "end": end, "days": t["days"],
        "primary_metric": args.primary, "guardrails": [g for g in args.guardrails.split(",") if g],
        "budget": about["targeting"]["budget"]})
    soft = pd.read_csv(data / "soft_launch_customers.csv")
    soft["used_block"] = soft["turned_on_new_look"]
    write_run(runs / "final-soft", {"customers": soft}, {
        "scenario": "final-soft", "about": "the soft launch of the 'complete the look' block: an opt-in toggle, "
        "28 days before the test (no test)", "treatment": "used_block (a copy of turned_on_new_look)",
        "outcome": "revenue"})
    print(f"Files: all right ({data}).")
    print(f"Wrote {runs / 'final-test'}: customers ({test['customers']['rows']:,} rows), visits "
          f"({test['visits']['rows']:,} rows), targets ({test['targets']['rows']:,} rows). Primary metric: "
          f"{args.primary}; guardrails: {args.guardrails or 'none'}.")
    print(f"Wrote {runs / 'final-soft'}: customers ({len(soft):,} rows), treatment used_block "
          f"(= turned_on_new_look).")
    print("Synthetic data. There is no true effect in these runs: xp check cannot help here.")


if __name__ == "__main__":
    main()
