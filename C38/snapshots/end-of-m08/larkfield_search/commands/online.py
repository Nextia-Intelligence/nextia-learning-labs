"""search bench and search interleave: latency, cost and online tests (Module 8)."""

import numpy as np

from .. import bench, data, interleave


class Bench:
    NAME = "bench"
    HELP = "Measure the time of each search stage on this computer (live models), and the cost per 1,000 queries."

    @staticmethod
    def add(p):
        p.add_argument("--queries", type=int, default=30, help="how many test queries (default 30)")
        p.add_argument("--threads", type=int, default=4, help="CPU threads for the models (default 4)")
        p.add_argument("--rerank", type=int, default=50, help="candidates for the cross-encoder (0: skip it)")

    @staticmethod
    def run(args):
        q = data.split("test")
        q = q[q["source"] == "wands"]["query"].head(args.queries).tolist()
        times = bench.stages(q, args.rerank, args.threads)
        s = bench.summary(times)
        print(f"{len(q)} test queries, models on {args.threads} thread(s); milliseconds per query:")
        print(f"{'stage':<26}{'p50':>9}{'p95':>9}")
        for k, v in s.items():
            print(f"{k:<26}{v['p50']:>9.1f}{v['p95']:>9.1f}")
        hybrid = sum(np.array(times[k]) for k in ("understand", "lexical", "encode", "dense search", "fusion"))
        designs = {"hybrid": hybrid}
        if f"rerank {args.rerank}" in times:
            designs[f"hybrid + rerank {args.rerank}"] = hybrid + np.array(times[f"rerank {args.rerank}"])
        designs["ltr (hybrid inside)"] = np.array(times["ltr features and model"]) + np.array(times["encode"])
        print(f"\n{'design':<26}{'p50 ms':>9}{'p95 ms':>9}{'US$ per 1,000':>15}")
        for name, v in designs.items():
            p50, p95 = np.percentile(v, 50), np.percentile(v, 95)
            print(f"{name:<26}{p50:>9.1f}{p95:>9.1f}{bench.usd_per_1000(p50, args.threads):>15.5f}")
        for k, v in bench.sizes().items():
            print(f"{k}: {v:.1f} MB")


class Interleave:
    NAME = "interleave"
    HELP = "Simulate team-draft interleaving and an A/B test between two runs with the click model."

    @staticmethod
    def add(p):
        p.add_argument("a")
        p.add_argument("b")
        p.add_argument("--seeds", type=int, default=5)

    @staticmethod
    def run(args):
        lists = interleave.ranked_lists(args.a, args.b)
        res = [interleave.simulate(lists, seed) for seed in range(args.seeds)]
        print(f"A = {args.a}, B = {args.b}; {len(lists)} test queries; clicks from the click model (synthetic)")
        for i, r in enumerate(res):
            print(f"seed {i}: interleaving clear after {r['interleaving'] or 'more than ' + str(r['searches'])} "
                  f"searches (winner {r.get('winner_interleaving', '-')}); A/B test clear after "
                  f"{r['ab'] or 'more than ' + str(r['searches'])} searches (winner {r.get('winner_ab', '-')})")
        il = [r["interleaving"] for r in res if r["interleaving"]]
        ab = [r["ab"] for r in res if r["ab"]]
        print(f"median searches: interleaving {np.median(il) if il else 'n/a'}, A/B {np.median(ab) if ab else 'n/a'}")


COMMANDS = [Bench, Interleave]
