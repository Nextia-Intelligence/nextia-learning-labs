"""xp prompt: the offline evaluation of the two prompts (--offline), then the online test's result per ticket,
with tickets grouped by customer (the randomisation unit)."""

import pandas as pd

from ..runs import load_run
from ..stats import diff_ratio
from ..support import graded

NAME = "prompt"
HELP = "the support-assistant prompt test: offline grades (--offline) or the online result per ticket"
METRICS = [("resolved", "resolved by the assistant"), ("handoff", "handed to a person"),
           ("complaint", "complaint (guardrail)"), ("cost", "cost per ticket, dollars")]


def add(p):
    p.add_argument("run", nargs="?", default="prompt", help="a prompt run (default: the newest prompt run)")
    p.add_argument("--offline", action="store_true", help="grade the 120 recorded answers of each prompt")


def per_customer(t):
    """One row per customer (the randomisation unit): the number of tickets and the sum of each metric."""
    return t.groupby(["customer_id", "variant"]).agg(tickets=("ticket_id", "size"), resolved=("resolved", "sum"),
                                                     handoff=("handoff", "sum"), complaint=("complaint", "sum"),
                                                     cost=("cost", "sum")).reset_index()


def run(args):
    if args.offline:
        g = pd.DataFrame(graded())
        s = g.groupby("prompt")[["correct", "handoff", "unsafe", "words", "model_cost"]].mean()
        print("Offline evaluation: 120 recorded answers per prompt, graded by the rules in support.py.")
        for v, r in s.iterrows():
            print(f"  prompt {v}: correct {r.correct:.1%}, hands off {r.handoff:.1%}, unsafe {r.unsafe:.1%}, "
                  f"{r.words:.0f} words, model cost {r.model_cost * 1000:.3f} dollars per 1,000 answers")
        return
    run_ = load_run(args.run)
    t = run_.table("tickets")
    per = per_customer(t)
    a, b = per[per.variant == "A"], per[per.variant == "B"]
    print(f"Run {run_.folder.name}: {len(t):,} tickets from {len(per):,} customers "
          f"(A {len(a):,}, B {len(b):,} customers). Per ticket, B − A:")
    out = {}
    for m, label in METRICS:
        r = diff_ratio(a[m], a.tickets, b[m], b.tickets)
        out[m] = r
        print(f"  {label:<28} A {r['mean_a']:.4f}  B {r['mean_b']:.4f}  difference {r['difference']:+.4f} "
              f"(95% interval {r['low']:+.4f} to {r['high']:+.4f})")
    run_.save_analysis({"command": NAME, "metrics": out})


def check(analysis, truth):
    lines = ["True effects per ticket (from the simulator) against your intervals:"]
    for m, _ in METRICS:
        r, eff = analysis["metrics"][m], truth[m]["effect"]
        lines.append(f"  {m:<9} true {eff:+.4f}, yours {r['low']:+.4f} to {r['high']:+.4f}: "
                     f"{'contains it' if r['low'] <= eff <= r['high'] else 'MISSES it'}")
    return lines
