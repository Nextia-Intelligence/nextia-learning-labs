"""route corrections: the queue moves that agents made (data/corrections.csv) are new labels, but a quick move is
not always a right one. This command lists the moves to check before they become training labels: moves made in
less than 10 seconds, and moves to a route that the model finds very unlikely.

    route corrections                    a summary
    route corrections --write            also write queue/corrections_to_check.csv
"""

from pathlib import Path

import pandas as pd

from larkroute import data, tfidf
from larkroute.methods import as_proba

ROOT = Path(__file__).resolve().parents[2]


def to_check(corr: pd.DataFrame, proba: pd.DataFrame, quick_s: float = 10, unlikely: float = 0.05) -> pd.Series:
    p_to = [proba.at[i, r] if r in proba.columns else 0.0 for i, r in zip(corr.index, corr["to_route"], strict=True)]
    return (corr["seconds"] < quick_s) | (pd.Series(p_to, index=corr.index) < unlikely)


def run(args):
    corr = pd.read_csv(data.data_dir() / "corrections.csv")
    msgs = data.launch_month().set_index("message_id").loc[corr["message_id"]].reset_index()
    train = data.messages("train")
    model = tfidf.logistic_regression().fit(train["text"], train["route"])
    proba = as_proba(model.predict_proba(msgs["text"]), model.classes_)
    flag = to_check(corr, proba)
    print(f"{len(corr)} queue moves by {corr['agent'].nunique()} agents; {(corr['seconds'] < 10).sum()} made in less "
          f"than 10 seconds. To check before training: {int(flag.sum())} ({flag.mean():.0%}).")
    print(corr.groupby("to_route").size().rename("moves to").to_string())
    if args.write:
        out = ROOT / "queue" / "corrections_to_check.csv"
        out.parent.mkdir(exist_ok=True)
        corr[flag].to_csv(out, index=False)
        print(f"Written: {out.relative_to(ROOT)}")


def add(sub):
    p = sub.add_parser("corrections", help="check the agents' queue moves before they become labels")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=run)
