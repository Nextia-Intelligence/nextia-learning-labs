"""xp synth: a synthetic Quebec from a weighted mix of the other provinces, and placebo tests."""

import numpy as np

from ..runs import load_run
from ..synth import synth_effect

NAME = "synth"
HELP = "synthetic control on the regions run, with a placebo test for every other province"


def add(p):
    p.add_argument("run", nargs="?", default="regions", help="a regions run (default: the newest regions run)")


def run(args):
    run_ = load_run(args.run)
    df = run_.table("provinces_weekly")
    treated, start = run_.meta["events"]["treated"], run_.meta["events"]["rollout"]
    wide = df.pivot(index="week", columns="province", values="revenue").sort_index()
    pre = np.asarray(wide.index < start)
    series = {p: np.log(wide[p].to_numpy()) for p in wide.columns}
    r = synth_effect(series, treated, pre)
    print(f"Synthetic {treated}: " + ", ".join(f"{p} {w:.2f}" for p, w in sorted(r["weights"].items(),
                                                                                 key=lambda kv: -kv[1]) if w >= 0.01))
    print(f"  Fit before the change: RMSPE {r['rmspe_pre']:.4f} (log sales). Effect after: {r['effect']:+.1%}.")
    placebos = {}
    for p in wide.columns:
        if p == treated:
            continue
        others = {u: s for u, s in series.items() if u != treated}
        placebos[p] = synth_effect(others, p, pre)
    ratios = sorted([(v["ratio"], p) for p, v in placebos.items()] + [(r["ratio"], treated)], reverse=True)
    rank = [p for _, p in ratios].index(treated) + 1
    print(f"  Placebo test: post/pre gap ratio {r['ratio']:.1f} for {treated}; rank {rank} of {len(ratios)} "
          f"(p = {rank / len(ratios):.2f}). Placebo effects: "
          + ", ".join(f"{p} {v['effect']:+.1%}" for p, v in placebos.items()))
    run_.save_analysis({"command": NAME, "estimate": r["effect"], "weights": r["weights"], "rank": rank,
                        "p": rank / len(ratios), "placebo_effects": {p: v["effect"] for p, v in placebos.items()},
                        "gap": r["gap"]})


def check(analysis, truth):
    t = truth["effect"]["relative"]
    return [f"True effect (from the simulator): {t:+.1%} on Quebec's weekly sales.",
            f"Your synthetic control: {analysis['estimate']:+.1%}, {analysis['estimate'] - t:+.1%} from the truth "
            f"(placebo p = {analysis['p']:.2f})."]
