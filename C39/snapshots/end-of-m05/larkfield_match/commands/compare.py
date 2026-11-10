"""match compare: two runs side by side, and the pairs where they disagree."""

from .. import data, evaluate, pairs, runs

NAME = "compare"
HELP = "Compare two runs on a split: precision and recall of each, and examples of pairs that only one finds."


def add(p):
    p.add_argument("run_a")
    p.add_argument("run_b")
    p.add_argument("--split", default="test", choices=["train", "validation", "test", "all"])
    p.add_argument("--show", type=int, default=3, help="how many example pairs to show for each side")


def run(args):
    ds = runs.get(args.run_a)[0]
    if runs.get(args.run_b)[0] != ds:
        raise SystemExit("The two runs match different datasets.")
    a, b = pairs.get(args.run_a), pairs.get(args.run_b)
    for name, df in ((args.run_a, a), (args.run_b, b)):
        m = evaluate.pair_measures(df, ds, args.split)
        print(f"{name:<22} precision {m['precision']:.3f}  recall {m['recall']:.3f}  F1 {m['f1']:.3f}  "
              f"({m['predicted']:,} pairs)")
    la = evaluate.label_pairs(evaluate.ordered(a[a["match"] == 1]), ds)
    lb = evaluate.label_pairs(evaluate.ordered(b[b["match"] == 1]), ds)
    if args.split != "all":
        la, lb = la[la.split == args.split], lb[lb.split == args.split]
    ka = set(zip(la.record_id_l, la.record_id_r))
    kb = set(zip(lb.record_id_l, lb.record_id_r))
    only_a = la[[k not in kb for k in zip(la.record_id_l, la.record_id_r)]]
    only_b = lb[[k not in ka for k in zip(lb.record_id_l, lb.record_id_r)]]
    names = _names(ds)
    for title, df in ((f"Only {args.run_a}", only_a), (f"Only {args.run_b}", only_b)):
        print(f"{title}: {len(df):,} pairs ({int(df.same.sum()):,} right, {int((1 - df.same).sum()):,} wrong)")
        for r in df.sort_values("same").head(args.show).itertuples():
            print(f"  {'right' if r.same else 'wrong'}  {r.record_id_l} {names.get(r.record_id_l, '')!r}  /  "
                  f"{r.record_id_r} {names.get(r.record_id_r, '')!r}")


def _names(ds):
    if ds == "products":
        return {**dict(zip(data.feed("a").product_id, data.feed("a").title)),
                **dict(zip(data.feed("b").product_id, data.feed("b").title))}
    r = data.records()
    return dict(zip(r.record_id, r.name))
