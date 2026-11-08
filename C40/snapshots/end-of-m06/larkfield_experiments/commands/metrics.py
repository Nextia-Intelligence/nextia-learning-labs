"""xp metrics: every metric of a test at once, with corrections for many tests (Bonferroni, Benjamini–Hochberg)."""

import numpy as np

from ..metrics import metric_values, split
from ..runs import load_run
from ..stats import diff_means

NAME = "metrics"
HELP = "test every metric of a run, with Bonferroni and Benjamini-Hochberg corrections for many metrics"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--alpha", type=float, default=0.05)


def bonferroni(p, alpha=0.05):
    return np.asarray(p) < alpha / len(p)


def benjamini_hochberg(p, alpha=0.05):
    """True for the discoveries at a false discovery rate of alpha: sort the p-values, find the largest k with
    p_(k) <= k/m × alpha, and keep the k smallest."""
    p = np.asarray(p)
    m = len(p)
    order = np.argsort(p)
    below = p[order] <= alpha * np.arange(1, m + 1) / m
    keep = np.zeros(m, bool)
    if below.any():
        k = np.nonzero(below)[0].max()
        keep[order[: k + 1]] = True
    return keep


def run(args):
    run_ = load_run(args.run)
    df = run_.table("customers")
    names = run_.meta.get("metrics") or [run_.meta["primary_metric"]]
    a, b = split(df)
    results = [diff_means(metric_values(a, m), metric_values(b, m)) for m in names]
    p = [r["p"] for r in results]
    bon, bh = bonferroni(p, args.alpha), benjamini_hochberg(p, args.alpha)
    print(f"Run {run_.folder.name}: {len(names)} metrics. Primary metric: {run_.meta['primary_metric']}.")
    print(f"{'metric':<20} {'relative':>9} {'p':>8}  p<{args.alpha:g}  Bonferroni  BH")
    for m, r, bo, bhk in zip(names, results, bon, bh):
        print(f"{m:<20} {r['relative']:>+9.2%} {r['p']:>8.4f}  {'yes' if r['p'] < args.alpha else '-':>6}  "
              f"{'yes' if bo else '-':>10}  {'yes' if bhk else '-':>3}")
    wins = [m for m, x in zip(names, p) if x < args.alpha]
    print(f"Without a correction: {len(wins)} winner(s) {wins}. Bonferroni: {int(bon.sum())}. "
          f"Benjamini-Hochberg: {int(bh.sum())}.")
    run_.save_analysis({"command": NAME, "winners": wins, "bonferroni": [m for m, k in zip(names, bon) if k],
                        "bh": [m for m, k in zip(names, bh) if k], "p": dict(zip(names, p))})


def check(analysis, truth):
    real = [m for m, t in truth.items() if isinstance(t, dict) and t.get("effect")]
    false = [m for m in analysis["winners"] if m not in real]
    return [f"Metrics with a real effect (from the simulator): {', '.join(real) or 'none'}.",
            f"Your winners without a correction: {', '.join(analysis['winners']) or 'none'}; false winners: "
            f"{', '.join(false) or 'none'}.",
            f"After Benjamini-Hochberg: {', '.join(analysis['bh']) or 'none'}."]
