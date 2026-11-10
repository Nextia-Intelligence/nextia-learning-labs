"""search ltr: train the learning-to-rank model and show what it learned."""

from .. import ltr

NAME = "ltr"
HELP = "Train the LambdaMART model (LightGBM) on judgments or clicks, and show the feature importance."


def add(p):
    p.add_argument("action", choices=["train"])
    p.add_argument("--labels", default="judgments", choices=["judgments", "clicks", "clicks-ipw"])


def run(args):
    df, imp = ltr.train(args.labels)
    total = sum(imp.values()) or 1
    print(f"Trained LambdaMART on {df['query_id'].nunique()} training queries, {len(df):,} candidates "
          f"({int((df['label'] > 0).sum()):,} with a label above 0), labels: {args.labels}. "
          f"Saved {ltr.model_path(args.labels)}")
    print("Feature importance (share of the total gain):")
    for name, g in sorted(imp.items(), key=lambda kv: -kv[1]):
        print(f"  {name:<18} {g / total:6.1%}")
