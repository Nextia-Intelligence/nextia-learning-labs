"""recs tune: try settings of a method on the validation period only; never on the test period."""

import itertools
import json

from .. import harness, registry
from ..paths import outputs_dir

NAME = "tune"
HELP = "Try a grid of settings on the validation period, and keep the best one (the test period is not touched)."


def add(p):
    p.add_argument("method", help="for example als")
    p.add_argument("--grid", action="append", metavar="NAME=V1,V2", required=True,
                   help="a setting and its values, for example factors=32,64,128 (repeat for more settings)")
    p.add_argument("--quick", action="store_true")


def run(args):
    grid = {}
    for g in args.grid:
        key, _, vals = g.partition("=")
        grid[key] = [registry.parse_settings([f"x={v}"])["x"] for v in vals.split(",")]
    rows = []
    for combo in itertools.product(*grid.values()):
        s = dict(zip(grid, combo))
        res, _, _ = harness.run(args.method, "validation", quick=args.quick, settings=s)
        rows.append((res["recall"], res["ndcg"], s, res["fit_seconds"]))
        print(f"{json.dumps(s):<50} recall@10 {res['recall']:.3f}  NDCG@10 {res['ndcg']:.3f}  fit {res['fit_seconds']:.1f} s")
    best = max(rows, key=lambda r: r[0])
    out = outputs_dir() / f"best-{args.method}.json"
    out.write_text(json.dumps(best[2]) + "\n")
    print(f"Best on validation: {json.dumps(best[2])} (recall@10 {best[0]:.3f}); saved to {out}")
    print(f"Now test it once: recs evaluate {args.method} " + " ".join(f"--set {k}={v}" for k, v in best[2].items()))
