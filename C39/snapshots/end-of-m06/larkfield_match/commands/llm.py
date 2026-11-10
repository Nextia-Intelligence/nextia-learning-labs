"""match llm: the recorded language-model answers for the unsure pairs, and how often they are right."""

import pandas as pd

from .. import llm

NAME = "llm"
HELP = "Show how often chat-small's recorded answers are right, in the unsure band and on sure pairs; or one pair."


def add(p):
    p.add_argument("--dataset", default="customers", choices=["customers", "products"])
    p.add_argument("--pair", nargs=2, metavar=("RECORD_L", "RECORD_R"), help="show the prompt and answer of one pair")


def run(args):
    rec = llm.recorded(args.dataset)
    if not rec:
        raise SystemExit("No recorded answers in data/recorded/.")
    if args.pair:
        key = tuple(sorted(args.pair))
        for m in llm.messages(*key, args.dataset):
            print(f"[{m['role']}]\n{m['content']}\n")
        r = rec.get(key)
        print(f"[recorded answer]\n{r['text']}\n(true: {r['true']})" if r else "No recorded answer for this pair.")
        return
    df = pd.DataFrame(rec.values())
    print(f"{len(df):,} recorded answers from {df.model.iloc[0]}; US${df.usd.sum():.4f} in all, "
          f"US${df.usd.mean() * 1000:.3f} per 1,000 pairs; median {df.latency_s.median():.2f} s per answer")
    for why, g in df.groupby("why_sampled"):
        decided = g[g.answer != "unsure"]
        right = (decided.answer == decided.true).mean() if len(decided) else float("nan")
        print(f"  {why:<32} {len(g):>5} pairs: same {int((g.answer == 'same').sum())}, different "
              f"{int((g.answer == 'different').sum())}, unsure {int((g.answer == 'unsure').sum())}; "
              f"right on {right:.1%} of the decided pairs")
