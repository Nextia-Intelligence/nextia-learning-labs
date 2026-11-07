"""route compare: train and score methods on the same messages and the same cost table.

    route compare --quick                     everything to a person, the rules, and TF-IDF + logistic regression
    route compare                             every method that this project has
    route compare --methods "rules or a person,TF-IDF + Naive Bayes"
    route compare --methods "hosted LLM chat-small, few-shot (recorded);TF-IDF + linear SVM"
    route compare --split validation          choose on validation; report test once at the end
    route compare --labels old                train on the old system's queue labels (noisy)
"""

import json
import time
from pathlib import Path

import pandas as pd

from larkroute import costs as cost_table
from larkroute import data, metrics
from larkroute.methods import available, timed_predict

QUICK = ["everything to a person", "rules or a person", "TF-IDF + logistic regression"]
ROOT = Path(__file__).resolve().parents[2]


def train_labels(kind: str) -> pd.DataFrame:
    train = data.messages("train")
    if kind == "old":
        old = pd.read_csv(data.data_dir() / "old_queue.csv")
        train = train.drop(columns="route").merge(old.rename(columns={"old_queue": "route"}), on="message_id")
    return train


def compare(names, split="test", labels="reviewed", quiet=False) -> list[dict]:
    methods = available()
    unknown = [n for n in names if n not in methods]
    if unknown:
        raise SystemExit(f"Unknown method: {', '.join(unknown)}. Known: {', '.join(methods)}")
    train, truth = train_labels(labels), data.messages(split)
    compute = json.loads((ROOT / "config" / "compute.json").read_text())
    costs = cost_table.load()
    rows = []
    for name in names:
        m = methods[name]()
        t0 = time.perf_counter()
        m.fit(train)
        fit_s = time.perf_counter() - t0
        pred, ms = timed_predict(m, truth)
        ms = getattr(m, "meta", {}).get("ms_per_message", ms)  # a recorded method: the time measured when it ran
        row = metrics.score(name, truth, pred, run_cost_per_1000=m.run_cost_per_1000(ms, compute),
                            ms_per_message=ms, costs=costs)
        row["fit_s"] = round(fit_s, 1)
        rows.append(row)
        if not quiet:
            print(f"  {name}: done", flush=True)
    return rows


def method_names(text: str, known) -> list[str]:
    """Split the --methods text into method names. A semicolon always separates two names. A comma separates them
    too, except inside a known name that has a comma ("hosted LLM chat-small, few-shot (recorded)")."""
    if ";" in text:
        return [n.strip() for n in text.split(";") if n.strip()]
    names, part = [], ""
    for piece in text.split(","):
        part = f"{part},{piece}" if part else piece
        if part.strip() in known:
            names.append(part.strip())
            part = ""
        elif not any(k.startswith(part.strip() + ",") for k in known):
            names.append(part.strip())  # unknown: compare() names it in its error message
            part = ""
    if part.strip():
        names.append(part.strip())
    return names


def run(args):
    if args.quick:
        names = QUICK
    else:
        names = method_names(args.methods, set(available())) if args.methods else list(available())
    print(f"Scoring {len(names)} methods on the {args.split} messages (trained on the {args.labels} labels)...")
    rows = compare(names, args.split, args.labels)
    print(metrics.table(rows))
    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save).write_text(json.dumps(rows, indent=2) + "\n")
        print(f"Saved: {args.save}")


def add(sub):
    p = sub.add_parser("compare", help="compare routing methods on the same messages and costs")
    p.add_argument("--quick", action="store_true", help="only the three first methods (a few seconds)")
    p.add_argument("--methods", help="method names, separated by commas (or semicolons)")
    p.add_argument("--split", default="test", choices=["validation", "test"])
    p.add_argument("--labels", default="reviewed", choices=["reviewed", "old"])
    p.add_argument("--save", help="write the rows to this JSON file")
    p.set_defaults(func=run)
