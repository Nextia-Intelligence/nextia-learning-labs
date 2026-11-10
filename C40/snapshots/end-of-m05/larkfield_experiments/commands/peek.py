"""xp peek: look at a test every day, as a dashboard does. With --aa-tests, simulate many A/A tests and count
how often daily peeking finds a false winner, against a fixed-length test and a sequential test."""

import numpy as np
import pandas as pd
from scipy import stats

from ..runs import load_run
from ..sequential import sequential_path

NAME = "peek"
HELP = "the result day by day (fixed-length p-value and the sequential test), or --aa-tests N simulated A/A tests"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--metric", default="revenue", help="revenue or ordered (per customer, up to that day)")
    p.add_argument("--tau", type=float, default=None,
                   help="the sequential test's guess of a real effect's size (default: 5%% of the mean)")
    p.add_argument("--aa-tests", type=int, dest="aa_tests", help="simulate N A/A tests with daily looks")
    p.add_argument("--days", type=int, default=28)
    p.add_argument("--per-day", type=int, dest="per_day", default=2000, help="new customers per group per day")
    p.add_argument("--seed", type=int, default=0)


def daily_looks(visits: pd.DataFrame, metric: str) -> pd.DataFrame:
    """For each day: the customers seen so far, and the difference of their means up to that day."""
    rows = []
    for day in sorted(visits["date"].unique()):
        so_far = visits[visits["date"] <= day]
        col = "ordered" if metric == "ordered" else "revenue"
        per = so_far.groupby(["customer_id", "variant"])[col].sum().reset_index()
        if metric == "ordered":
            per[col] = (per[col] > 0).astype(int)
        a, b = per.loc[per.variant == "A", col], per.loc[per.variant == "B", col]
        va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        d = b.mean() - a.mean()
        p = 2 * stats.norm.sf(abs(d) / np.sqrt(va + vb))
        rows.append({"date": day, "n_a": len(a), "n_b": len(b), "mean_a": a.mean(), "difference": d,
                     "variance": va + vb, "p": p})
    return pd.DataFrame(rows)


def run(args):
    if args.aa_tests:
        return simulate_aa(args)
    run_ = load_run(args.run)
    looks = daily_looks(run_.table("visits"), args.metric)
    tau = args.tau if args.tau is not None else 0.05 * looks["mean_a"].iloc[-1]
    path = sequential_path(looks["difference"], looks["variance"], tau**2)
    looks["seq_low"], looks["seq_high"], looks["seq_p"] = zip(*path)
    print(f"Run {run_.folder.name}, metric {args.metric}: one look a day. 'fixed p' is the usual test at that day; "
          f"the sequential columns are valid at every look (tau {tau:.3g}).")
    print(f"{'day':>3} {'date':<10} {'customers':>9} {'difference':>10} {'fixed p':>8}   sequential interval   seq. p")
    first_win = first_seq = None
    for i, r in looks.iterrows():
        mark = " <" if r.p < 0.05 else ""
        print(f"{i + 1:>3} {r.date:<10} {r.n_a + r.n_b:>9,} {r.difference:>+10.4f} {r.p:>8.3f}   "
              f"{r.seq_low:>+9.4f} to {r.seq_high:>+8.4f} {r.seq_p:>8.3f}{mark}")
        if r.p < 0.05 and first_win is None:
            first_win = i + 1
        if r.seq_p < 0.05 and first_seq is None:
            first_seq = i + 1
    print(f"First day with p < 0.05 (peeking): {first_win or 'none'}. First day the sequential test decides: "
          f"{first_seq or 'none'}.")
    last = looks.iloc[-1]
    run_.save_analysis({"command": NAME, "metric": args.metric, "first_peek_win": first_win,
                        "first_sequential": first_seq, "difference": float(last.difference),
                        "low": float(last.seq_low), "high": float(last.seq_high), "p_fixed_end": float(last.p)})


def simulate_aa(args):
    """N A/A tests of a 0/1 metric (an order, 22% of customers), per_day new customers per group per day."""
    rng = np.random.default_rng(args.seed)
    n, days, rate = args.aa_tests, args.days, 0.22
    xa = rng.binomial(args.per_day, rate, (n, days)).cumsum(axis=1)
    xb = rng.binomial(args.per_day, rate, (n, days)).cumsum(axis=1)
    m = args.per_day * np.arange(1, days + 1)
    pa, pb = xa / m, xb / m
    pool = (xa + xb) / (2 * m)
    v = pool * (1 - pool) * 2 / m
    z = (pb - pa) / np.sqrt(v)
    p = 2 * stats.norm.sf(np.abs(z))
    tau = 0.05 * rate
    fixed = (p[:, -1] < 0.05).mean()
    peek = (p < 0.05).any(axis=1).mean()
    seq = np.mean([min(r[2] for r in sequential_path(pb[i] - pa[i], v[i], tau**2)) < 0.05 for i in range(n)])
    weekly = (p[:, 6::7] < 0.05).any(axis=1).mean()
    print(f"{n:,} simulated A/A tests (no real effect), {days} days, {args.per_day:,} new customers per group a day:")
    print(f"  fixed length, one look at day {days}:   {fixed:.1%} false winners")
    print(f"  peeking once a week, stop at p < 0.05: {weekly:.1%} false winners")
    print(f"  peeking every day, stop at p < 0.05:  {peek:.1%} false winners")
    print(f"  sequential test, look every day:      {seq:.1%} false winners")
