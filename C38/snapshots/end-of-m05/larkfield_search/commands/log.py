"""search log: read the synthetic query log."""

from .. import data

NAME = "log"
HELP = "Read the synthetic query log: the most common queries, the long tail and the zero-result searches."


def add(p):
    p.add_argument("--top", type=int, default=10, help="how many queries to list (default 10)")
    p.add_argument("--zero", action="store_true", help="list the most common queries that returned nothing")


def run(args):
    s = data.searches()
    counts = s["query"].value_counts()
    zero = s[s["results"] == 0]
    once = int((counts == 1).sum())
    print(f"{len(s):,} searches (synthetic), {len(counts):,} different queries; "
          f"{once:,} queries were searched only once")
    print(f"Zero-result searches: {len(zero):,} ({len(zero) / len(s):.1%}); with a click: "
          f"{(s['clicks'] > 0).mean():.1%} of searches")
    if args.zero:
        print("\nMost common zero-result queries:")
        for q, n in zero["query"].value_counts().head(args.top).items():
            print(f"{n:6}  {q}")
        return
    top = counts.head(args.top)
    print(f"\nThe {args.top} most common queries make {top.sum() / len(s):.1%} of searches:")
    for q, n in top.items():
        print(f"{n:6}  {q}")
