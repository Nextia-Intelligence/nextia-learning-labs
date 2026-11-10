"""match review: the review queue, what the reviewer sees, a day of decisions, and retraining with them."""

from .. import evaluate, incremental, review, thresholds
from ..runs import learned

NAME = "review"
HELP = "Show the review queue (--show N), let the simulated reviewer decide a day of pairs (--decide), or retrain."


def add(p):
    p.add_argument("--show", type=int, default=0, help="show the N most likely pairs as the reviewer sees them")
    p.add_argument("--decide", action="store_true", help="the simulated reviewer decides one day of pairs")
    p.add_argument("--capacity", type=int, default=300)
    p.add_argument("--error", type=float, default=0.02, help="share of the reviewer's decisions that are wrong")
    p.add_argument("--retrain", action="store_true", help="retrain lgbm with the review labels and compare")


def run(args):
    q = review.queue()
    print(f"Review queue: {len(q):,} pairs" + (f" ({', '.join(f'{k} {v}' for k, v in q.reason.value_counts().items())})"
                                              if len(q) else ""))
    if args.show:
        print(review.show(args.show))
    if args.decide:
        r = review.simulate(args.capacity, args.error)
        print(f"Decided {r['decided']} pairs: {r['same']} same, {r['different']} different "
              f"({r['reviewer_mistakes']} reviewer mistakes, simulated); {r['left_in_queue']:,} left in the queue")
    if args.retrain:
        extra = review.labels()
        known = incremental.known_records()
        # the retrained model goes to its own file, outputs/models/lgbm-review.pkl: lgbm.pkl stays the model of
        # `match train`, which `match daily` uses
        for name, ex in (("without review labels", None), (f"with {len(extra)} review labels", extra)):
            s = learned.scores("lgbm", "customers", ex, known, name="lgbm-review", save=ex is not None)
            m = evaluate.pair_measures(thresholds.decide(s, thresholds.best_f1(s, "customers")), "customers", "test")
            print(f"  lgbm {name}: test precision {m['precision']:.3f}, recall {m['recall']:.3f}, F1 {m['f1']:.3f}")
        print("Saved the retrained model in outputs/models/lgbm-review.pkl (outputs/models/lgbm.pkl is unchanged)")
