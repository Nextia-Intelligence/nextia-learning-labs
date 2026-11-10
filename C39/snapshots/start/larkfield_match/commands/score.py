"""match score: run a matcher and keep its pairs."""

from .. import pairs, runs

NAME = "score"
HELP = "Run a matcher (--run NAME) and save the pairs it calls the same. --list shows every run."


def add(p):
    p.add_argument("--run", default="exact")
    p.add_argument("--list", action="store_true", help="list the runs you can use")


def run(args):
    if args.list:
        for name, (ds, _, desc) in sorted(runs.all_runs().items()):
            print(f"  {name:<22} {ds:<10} {desc}")
        return
    df = pairs.get(args.run, rebuild=True)
    print(f"Saved {len(df):,} scored pairs to {pairs.path(args.run)}")
