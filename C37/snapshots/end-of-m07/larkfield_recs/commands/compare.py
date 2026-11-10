"""recs compare: two saved runs on the same customers, with the difference and its 95% interval."""

import numpy as np

from .. import harness, metrics

NAME = "compare"
HELP = "Compare two saved runs (recs evaluate first) on the same customers: difference and 95% interval."


def add(p):
    p.add_argument("a", help="the first method (the baseline)")
    p.add_argument("b", help="the second method")
    p.add_argument("--period", default="test", choices=["test", "validation", "launch", "random"])
    p.add_argument("--quick", action="store_true")
    p.add_argument("--metric", default="recall", choices=list(harness.RANKING))
    p.add_argument("--by", choices=["segment"])


def run(args):
    ra, pa = harness.load_run(args.a, args.period, args.quick)
    rb, pb = harness.load_run(args.b, args.period, args.quick)
    if not np.array_equal(pa["users"], pb["users"]):
        raise SystemExit("The two runs scored different customers: run both with the same period and --quick setting.")
    if ra["k"] != rb["k"]:
        raise SystemExit(f"The two runs have lists of different lengths (k={ra['k']} and k={rb['k']}): "
                         "run both with the same --k.")
    m = args.metric
    a, b = pa[m], pb[m]
    mean, lo, hi = metrics.paired_difference(a, b)
    print(f"{m}@{ra['k']}: {args.a} {a.mean():.3f}, {args.b} {b.mean():.3f}")
    print(f"difference {mean:+.3f} (95% interval {lo:+.3f} to {hi:+.3f}); "
          f"better for {(b > a).sum():,} customers, worse for {(b < a).sum():,}, the same for {(b == a).sum():,}")
    print("The difference is " + ("clear: the interval does not include 0." if lo > 0 or hi < 0
                                  else "not clear: the interval includes 0."))
    print(f"coverage {ra['coverage']:.1%} -> {rb['coverage']:.1%}; novelty {ra['novelty']:.2f} -> {rb['novelty']:.2f}")
    if args.by == "segment":
        for seg in ("new", "occasional", "loyal"):
            mask = pa["segment"] == seg
            if mask.any():
                d, l, h = metrics.paired_difference(a[mask], b[mask])
                print(f"  {seg:<11}{mask.sum():>6,} customers  {d:+.3f} ({l:+.3f} to {h:+.3f})")
