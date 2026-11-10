"""search compare: is run B really better than run A? A paired comparison on the same queries."""

import pandas as pd

from .. import compare, data, engine, settings

NAME = "compare"
HELP = "Compare two runs on the same queries: the difference in NDCG@10 with its 95% interval, by slice too."


def add(p):
    p.add_argument("a", help="the run you have now")
    p.add_argument("b", help="the run you want to try")
    p.add_argument("--split", default="test", choices=["train", "validation", "test"])
    p.add_argument("--by", help="also compare by a query column: band, language, source, qtype, has_number")
    p.add_argument("--measure", default="ndcg@10")
    p.add_argument("--set", action="append", metavar="NAME=VALUE")


def run(args):
    settings.parse(args.set)
    a, _ = engine.evaluate(args.a, args.split)
    b, _ = engine.evaluate(args.b, args.split)
    d = compare.paired(a, b, args.measure)
    print(f"{args.b} minus {args.a} on {d['queries']} {args.split} queries: {args.measure} "
          f"{d['difference']:+.3f} (95% interval {d['low']:+.3f} to {d['high']:+.3f}); "
          f"better on {d['better']}, worse on {d['worse']}, the same on {d['same']}")
    if args.by:
        q = data.split(args.split).set_index("query_id")[[args.by]]
        rows = []
        for value, ids in q.groupby(args.by).groups.items():
            ids = [i for i in ids if i in a.index]
            r = compare.paired(a.loc[ids], b.loc[ids], args.measure)
            rows.append({args.by: value, "queries": r["queries"], args.a: a.loc[ids, args.measure].mean(),
                         args.b: b.loc[ids, args.measure].mean(), "difference": r["difference"],
                         "low": r["low"], "high": r["high"], "worse": r["worse"]})
        print()
        print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
