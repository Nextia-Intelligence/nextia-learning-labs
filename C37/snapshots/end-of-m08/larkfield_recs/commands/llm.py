"""recs llm: replay the recorded language-model answers (no key needed) and score them."""

import json

import numpy as np

from .. import data, metrics
from ..paths import data_dir

NAME = "llm"
HELP = "Score recorded chat-small answers: re-ranking the ranker's top 20, and naming products with no list."


def add(p):
    p.add_argument("what", choices=["rerank", "freeform"], nargs="?", default="rerank")


def _rows(name):
    f = data_dir() / "recorded" / f"llm_{name}.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def run(args):
    shop = data.load()
    p = data.Period(shop, "test")
    truth = {shop.customer_ids[u]: set(t.tolist()) for u, t in zip(p.users, p.truth)}
    rows = _rows(args.what)
    ok = [r for r in rows if r.get("answer")]
    secs = np.array([r["seconds"] for r in ok])
    usd = np.mean([r["usd"] for r in ok])
    print(f"Recorded answers from chat-small: {len(rows)} customers; refused by the provider's content filter: "
          f"{len(rows) - len(ok)}")
    print(f"Time per call p50 {np.percentile(secs, 50):.1f} s, p95 {np.percentile(secs, 95):.1f} s; "
          f"US${usd * 1000:.2f} per 1,000 customers")
    if args.what == "rerank":
        base, llm, bad = [], [], 0
        for r in ok:
            cand = [c["id"] for c in r["candidates"]]
            ranking = [x for x in r["answer"].get("ranking", []) if isinstance(x, str)]
            bad += sum(1 for x in ranking if x not in cand)
            valid = list(dict.fromkeys(x for x in ranking if x in cand))[:10]
            t = truth[r["customer"]]
            idx = lambda ids: np.array([shop.product_index[i] for i in ids])
            base.append(metrics.recall_at_k(idx(cand[:10]), list(t)))
            llm.append(metrics.recall_at_k(idx(valid) if valid else np.array([-1]), list(t)))
        d, lo, hi = metrics.paired_difference(base, llm)
        print(f"recall@10 on these customers: ranker {np.mean(base):.3f}, ranker + LLM re-ranking {np.mean(llm):.3f}; "
              f"difference {d:+.3f} (95% interval {lo:+.3f} to {hi:+.3f})")
        print(f"IDs not in the candidate list (made up or changed): {bad}")
        r = ok[0]
        reasons = r["answer"].get("reasons", {})
        print(f"Example reasons for {r['customer']}:")
        for pid, why in list(reasons.items())[:3]:
            title = shop.products.title[shop.product_index[pid]] if pid in shop.product_index else "(not a real product)"
            print(f"  {pid} {title}: {why}")
    else:
        titles = {t.lower(): i for i, t in enumerate(shop.products.title)}
        named = found = seen = hits = 0
        for r in ok:
            own = {h["title"].lower() for h in r["history"]}
            for name in r["answer"].get("products", [])[:10]:
                named += 1
                key = str(name).lower().strip()
                i = titles.get(key)
                if i is not None:
                    found += 1
                    seen += key in own
                    hits += i in truth[r["customer"]]
        print(f"Products named: {named}; exact titles that exist in the catalogue: {found} ({found / max(named, 1):.0%}), "
              f"{seen} of them copied from the customer's own history; the other {named - found} do not exist")
        print(f"Named products that the customer ordered in the test period: {hits}")
        print("Example: " + "; ".join(str(x) for x in ok[0]["answer"].get("products", [])[:4]))
