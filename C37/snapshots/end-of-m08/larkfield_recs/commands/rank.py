"""recs rank: train the LambdaMART ranker and show what it learned."""

from .. import data, registry

NAME = "rank"
HELP = "Train the two-stage ranker (LightGBM LambdaMART) and show the training data and the most important features."


def add(p):
    p.add_argument("--period", default="test", choices=["test", "validation"])
    p.add_argument("--set", action="append", metavar="NAME=VALUE", help="for example negatives=20 or trees=100")
    p.add_argument("--top", type=int, default=10)


def run(args):
    shop = data.load()
    p = data.Period(shop, args.period, quick=True)
    m = registry.make("two-stage", p, registry.parse_settings(args.set)).fit()
    print(f"Trained on the two weeks before {p.cutoff}: {m.train_customers:,} customers, {m.train_rows:,} candidate rows, "
          f"{m.train_positives:,} ordered (label 1); candidates found {m.train_candidate_recall:.1%} of the ordered products")
    print(f"Fit time (both stages, two cut-offs): {m.fit_seconds:.1f} s")
    print("Most important features (share of the total gain):")
    for name, g in m.importance[: args.top]:
        print(f"  {name:<24}{g:>7.1%}")
