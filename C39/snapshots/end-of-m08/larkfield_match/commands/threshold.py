"""match threshold: precision and recall of a scored run at several thresholds (validation pairs)."""

import numpy as np

from .. import pairs, runs, thresholds

NAME = "threshold"
HELP = "Show precision and recall at several thresholds of a run's score, on the validation pairs."


def add(p):
    p.add_argument("--run", default="weighted")
    p.add_argument("--split", default="validation", choices=["train", "validation", "test"])
    p.add_argument("--steps", type=int, default=8)


def run(args):
    ds = runs.get(args.run)[0]
    df = pairs.get(args.run)
    t, p, r = thresholds.curve(df, ds, args.split)
    best = thresholds.best_f1(df, ds, args.split)
    picks = sorted(set(np.linspace(t.min(), t.max(), args.steps)) | {best})
    print(f"{args.run} on the {args.split} pairs:")
    print(f"  {'threshold':>10} {'precision':>10} {'recall':>8} {'F1':>6}")
    for x in picks:
        i = int(np.where(t >= x - 1e-9)[0][-1])
        f1 = 2 * p[i] * r[i] / (p[i] + r[i]) if p[i] + r[i] else 0
        mark = "  <- best F1" if x == best else ""
        print(f"  {t[i]:>10.3f} {p[i]:>10.3f} {r[i]:>8.3f} {f1:>6.3f}{mark}")
