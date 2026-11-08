"""search eval: measure a run on the judged queries."""

from .. import compare, data, engine, runs, settings

NAME = "eval"
HELP = "Measure a run on the judged queries: NDCG@10 with its 95% interval, recall@100, MRR, zero results."


def add(p):
    p.add_argument("--run", default="bm25", help="the run to measure")
    p.add_argument("--split", default="test", choices=["train", "validation", "test"])
    p.add_argument("--by", help="also show NDCG@10 by a query column: band, language, source, qtype, has_number")
    p.add_argument("--set", action="append", metavar="NAME=VALUE", help="change a setting of the run (repeatable)")
    p.add_argument("--list", action="store_true", help="list the runs and stop")


def report(name, split, pq, ms):
    s = compare.summary(pq)
    p50, p95 = compare.latency(ms)
    print(f"{name} on {s['queries']} {split} queries: NDCG@10 {s['ndcg@10']:.3f} "
          f"(95% interval {s['ndcg@10 low']:.3f} to {s['ndcg@10 high']:.3f})")
    print(f"recall@100 {s['recall@100']:.3f}, MRR {s['mrr']:.3f}, zero results {s['zero-result rate']:.1%}, "
          f"judged in the top 10 {s['judged@10']:.1%}; {p50:.1f} ms a query (p50), {p95:.1f} ms (p95)")


def run(args):
    if args.list:
        for name, r in sorted(runs.load().items(), key=lambda kv: (kv[1]["module"], kv[0])):
            print(f"{name:<24} {r['module']}  {r['about']}")
        return
    settings.parse(args.set)
    pq, ms = engine.evaluate(args.run, args.split)
    report(args.run, args.split, pq, ms)
    if args.by:
        t = compare.by_slice(pq, data.split(args.split), args.by)
        print()
        print(t.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
