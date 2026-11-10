"""match bands: two thresholds make three bands: match, review and non-match."""

from .. import evaluate, pairs, runs

NAME = "bands"
HELP = "Split a run's scored pairs into match, review and non-match bands with two thresholds (default: splink)."


def add(p):
    p.add_argument("--run", default="splink")
    p.add_argument("--lower", type=float, default=10.0, help="score below this: non-match (Splink: a match weight)")
    p.add_argument("--upper", type=float, default=20.0, help="score at or above this: match")
    p.add_argument("--split", default="test", choices=["train", "validation", "test", "all"])


def run(args):
    ds = runs.get(args.run)[0]
    s = evaluate.label_pairs(evaluate.ordered(pairs.get(args.run)), ds)
    if args.split != "all":
        s = s[s.split == args.split]
    n_true = int((evaluate.true_pairs(ds).split == args.split).sum()) if args.split != "all" \
        else len(evaluate.true_pairs(ds))
    auto = s[s.score >= args.upper]
    review = s[(s.score >= args.lower) & (s.score < args.upper)]
    print(f"{args.run}, {args.split} split, thresholds {args.lower} and {args.upper}:")
    print(f"  match band:     {len(auto):>7,} pairs, precision {auto.same.mean():.3f}")
    print(f"  review band:    {len(review):>7,} pairs ({int(review.same.sum()):,} true pairs, "
          f"{int((1 - review.same).sum()):,} not)")
    print(f"  non-match band: {len(s) - len(auto) - len(review):>7,} pairs, "
          f"{int(s[s.score < args.lower].same.sum()):,} true pairs lost there")
    found = int(auto.same.sum()) + int(review.same.sum())
    print(f"If reviewers decide every review pair correctly: precision {found / max(len(auto) + int(review.same.sum()), 1):.3f}, "
          f"recall {found / max(n_true, 1):.3f}")
