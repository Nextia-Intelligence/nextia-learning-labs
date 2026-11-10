"""recs batch: compute every known customer's suggestions now (the nightly job)."""

import time

from .. import serving

NAME = "batch"
HELP = "Train a method on the whole log and write every customer's top 50, the fallback and product neighbours."


def add(p):
    p.add_argument("method", nargs="?", default="two-stage")


def run(args):
    t0 = time.perf_counter()
    meta = serving.build(args.method)
    print(f"Batch: {args.method}, trained on the events before {meta['trained_on_events_before']}; "
          f"lists for {meta['customers']:,} customers; {time.perf_counter() - t0:.0f} s")
    print(f"Written to {serving.batch_dir()}/ (lists.npz, fallback.json, meta.json)")
