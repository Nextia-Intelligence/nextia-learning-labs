"""match allpairs: how long would comparing every pair take?"""

import time

import numpy as np

from .. import prepared

NAME = "allpairs"
HELP = "Time a name comparison on random pairs and estimate the time for all pairs of the customer records."


def add(p):
    p.add_argument("--sample", type=int, default=200_000, help="how many random pairs to time")


def run(args):
    df = prepared.customers()
    names = df.full.tolist()
    n = len(names)
    rng = np.random.default_rng(1)
    a = rng.integers(0, n, args.sample)
    b = rng.integers(0, n, args.sample)
    t0 = time.perf_counter()
    same = 0
    for i, j in zip(a, b):
        same += _similar(names[i], names[j])
    secs = time.perf_counter() - t0
    total = n * (n - 1) // 2
    per = secs / args.sample
    print(f"{n:,} records -> {total:,} pairs")
    print(f"Timed {args.sample:,} random pairs: {per * 1e6:.2f} microseconds per pair (one CPU core)")
    print(f"All pairs would take about {total * per / 3600:.1f} hours for one simple comparison of the names")
    print(f"Only to store the pairs as two 4-byte numbers each: {total * 8 / 1e9:.1f} GB of memory")


def _similar(x, y):
    """A small pure-Python comparison: the share of letters in common (the timing is the point, not the score)."""
    sx, sy = set(x), set(y)
    return len(sx & sy) / (len(sx | sy) or 1) > 0.8
