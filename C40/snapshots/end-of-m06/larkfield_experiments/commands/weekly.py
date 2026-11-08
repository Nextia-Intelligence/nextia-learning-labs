"""xp weekly: the effect week by week, by calendar week and by weeks since each customer's first visit. A
novelty effect shows as an effect that shrinks with the weeks since the first visit."""

import pandas as pd

from ..runs import load_run
from ..stats import diff_means

NAME = "weekly"
HELP = "the effect on revenue per visit by calendar week and by week since the customer's first visit"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")


def run(args):
    run_ = load_run(args.run)
    v = run_.table("visits")
    dates = pd.to_datetime(v["date"])
    v["week"] = ((dates - dates.min()).dt.days // 7 + 1).astype(int)
    first = v.groupby("customer_id")["date"].transform("min")
    v["week_since_first"] = ((dates - pd.to_datetime(first)).dt.days // 7 + 1).astype(int)
    out = {}
    for col, label in (("week", "calendar week"), ("week_since_first", "week since first visit")):
        print(f"Revenue per visit, B − A, by {label}:")
        out[col] = {}
        for w, part in v.groupby(col):
            r = diff_means(part.loc[part.variant == "A", "revenue"], part.loc[part.variant == "B", "revenue"])
            out[col][str(w)] = {k: r[k] for k in ("difference", "relative", "low", "high", "p")}
            bar = "#" * int(min(abs(r["relative"]) * 200, 30))
            print(f"  {w:>2}: {r['relative']:+7.1%} ({r['low']:+.3f} to {r['high']:+.3f}) {'+' if r['difference'] > 0 else '-'}{bar}")
    run_.save_analysis({"command": NAME, **out})


def check(analysis, truth):
    t = truth.get("by_week_since_first_visit")
    if not t:
        return ["This scenario has no true effect by week."]
    lines = ["Week since first visit: your estimate against the true effect (revenue per visit):"]
    for w, est in analysis["week_since_first"].items():
        if w in t:
            lines.append(f"  {w}: yours {est['relative']:+.1%}, true {t[w]['relative']:+.1%}")
    return lines
