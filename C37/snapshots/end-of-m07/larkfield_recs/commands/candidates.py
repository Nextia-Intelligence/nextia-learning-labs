"""recs candidates: how many of the ordered products each candidate source finds (the ranker's ceiling)."""

from .. import data, registry

NAME = "candidates"
HELP = "Show the share of ordered products that each candidate source finds, and all sources together."


def add(p):
    p.add_argument("--period", default="test", choices=["test", "validation"])
    p.add_argument("--quick", action="store_true")


def run(args):
    shop = data.load()
    p = data.Period(shop, args.period, quick=args.quick)
    m = registry.make("two-stage", p).fit()
    r = m.candidate_recall(p.users, p.truth)
    from ..methods.twostage import SOURCES
    print(f"{len(p.users):,} customers, {r['candidates_per_customer']:.0f} candidates per customer on average")
    print(f"{'source':<12}{'size':>6}{'ordered products found':>25}")
    for name, n in SOURCES.items():
        print(f"{name:<12}{n:>6}{r[name]:>25.1%}")
    print(f"{'all':<12}{'':>6}{r['all']:>25.1%}   <- no ranker can find more than this")
