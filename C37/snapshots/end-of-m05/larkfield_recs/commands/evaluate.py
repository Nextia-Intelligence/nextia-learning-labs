"""recs evaluate: score one method on a period with every measure."""

from .. import harness, registry

NAME = "evaluate"
HELP = "Score a method on the test period (or --period validation) and save the run for recs compare."


def add(p):
    p.add_argument("method", nargs="?", help="the method (recs evaluate --list shows them)")
    p.add_argument("--period", default="test", choices=["test", "validation", "launch", "random"],
                   help="test (default), validation (for tuning), launch (the new range's first two weeks) or "
                        "random (the leaky split, to see the mistake)")
    p.add_argument("--quick", action="store_true", help="score a fixed sample of 1,000 customers (faster)")
    p.add_argument("--k", type=int, default=10, help="length of each list (default 10)")
    p.add_argument("--set", action="append", metavar="NAME=VALUE", help="change a setting of the method")
    p.add_argument("--by", choices=["segment"], help="also show the results by customer segment")
    p.add_argument("--list", action="store_true", help="list the methods")


def run(args):
    if args.list or not args.method:
        for name, (_, _, desc) in registry.all_methods().items():
            print(f"{name:<18} {desc}")
        return
    res, _, _ = harness.run(args.method, args.period, args.k, args.quick, registry.parse_settings(args.set))
    harness.report(res, args.by)
