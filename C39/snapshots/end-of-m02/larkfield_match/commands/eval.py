"""match eval: pair precision and recall of a run against the true entities."""

from .. import evaluate, pairs, runs

NAME = "eval"
HELP = "Measure a run: pair precision, recall and F1 on a split (default test), and the number of entities."


def add(p):
    p.add_argument("--run", default="exact")
    p.add_argument("--split", default="test", choices=["train", "validation", "test", "all"])
    p.add_argument("--by", choices=["source", "problem"], help="also show recall and precision per group")
    p.add_argument("--rebuild", action="store_true", help="run the matcher again")


def run(args):
    ds = runs.get(args.run)[0]
    df = pairs.get(args.run, rebuild=args.rebuild)
    m = evaluate.pair_measures(df, ds, args.split)
    print(f"{args.run} on the {args.split} split: pair precision {m['precision']:.3f}, recall {m['recall']:.3f}, "
          f"F1 {m['f1']:.3f}")
    print(f"  {m['predicted']:,} pairs called the same: {m['tp']:,} right, {m['fp']:,} wrong; "
          f"{m['fn']:,} of {m['true']:,} true pairs missed")
    n = evaluate.entity_count(df, pairs.record_ids(ds))
    print(f"  entities after clustering (all records): {n:,} (true: {evaluate.true_entity_count(ds):,})")
    extra = getattr(_cluster_measures(), "report", None)
    if extra:
        extra(df, ds, args.split)
    if args.by:
        g = evaluate.by_group(df, ds, args.split, args.by)
        print(g.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


def _cluster_measures():
    """Module 7 adds cluster measures (clustermeasures.py); before that, eval shows pair measures only."""
    try:
        from .. import clustermeasures
        return clustermeasures
    except ImportError:
        return None
