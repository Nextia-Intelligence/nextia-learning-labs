"""match train: train a pair classifier on the labelled pairs and show what it uses."""

from .. import classifier, evaluate, thresholds
from ..runs import learned

NAME = "train"
HELP = "Train a pair classifier (logreg or lgbm) on the 3,000 labelled pairs; show its features and test results."


def add(p):
    p.add_argument("--model", default="lgbm", choices=list(classifier.MODELS))
    p.add_argument("--dataset", default="customers", choices=["customers", "products"])


def run(args):
    s = learned.scores(args.model, args.dataset)
    t = thresholds.best_f1(s, args.dataset)
    m = evaluate.pair_measures(thresholds.decide(s, t), args.dataset, "test")
    _, y = classifier.labelled_training_set(args.dataset)
    print(f"Trained {args.model} on {len(y):,} labelled pairs ({int(y.sum()):,} same); threshold {t:.3f} "
          f"(best F1 on validation)")
    print(f"Test: precision {m['precision']:.3f}, recall {m['recall']:.3f}, F1 {m['f1']:.3f}")
    name = f"{'p-' if args.dataset == 'products' else ''}{args.model}"
    imp = classifier.importance(learned.load(name), args.model, args.dataset)
    label = "share of gain" if args.model == "lgbm" else "coefficient (scaled inputs)"
    print(f"Features ({label}):")
    for f, v in imp.head(8).items():
        print(f"  {f:<16} {v:+.3f}")
