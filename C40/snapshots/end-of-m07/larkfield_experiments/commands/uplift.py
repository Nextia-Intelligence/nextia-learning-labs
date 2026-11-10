"""xp uplift: train an uplift model on the randomised email test, evaluate it with uplift and Qini curves, and
choose whom to email under a budget."""

import numpy as np

from ..runs import load_run
from ..uplift import fit_scores, qini_coefficient, uplift_curve

NAME = "uplift"
HELP = "uplift models (EconML T- and X-learner) against a 'who will buy' model on the email run, and a target list"


def add(p):
    p.add_argument("run", nargs="?", default="email", help="an email run (default: the newest email run)")
    p.add_argument("--learner", choices=["t", "x", "response"], default="t")
    p.add_argument("--budget", type=int, default=10_000, help="how many emails Rafael can send next month")
    p.add_argument("--seed", type=int, default=0, help="the random split into training (70%%) and test (30%%)")


def run(args):
    run_ = load_run(args.run)
    df, targets = run_.table("customers"), run_.table("targets")
    rng = np.random.default_rng(args.seed)
    test = rng.random(len(df)) < 0.3
    train, hold = df[~test], df[test]
    s_hold, s_targets = fit_scores(train, [hold, targets], args.learner)
    y, t = hold["ordered"].to_numpy(float), (hold["variant"] == "B").to_numpy(int)
    shares, gains = uplift_curve(s_hold, y, t)
    q = qini_coefficient(shares, gains)
    name = {"t": "T-learner", "x": "X-learner", "response": "'who will buy' model"}[args.learner]
    print(f"{name} trained on {len(train):,} customers of the test; evaluated on the other {len(hold):,}.")
    print("  Extra orders in the evaluation group if we email the top share by score (uplift curve):")
    for s, g in zip(shares[2::2], gains[2::2]):
        print(f"    top {s:>4.0%}: {g:+7.1f}")
    print(f"  Qini coefficient: {q:+.2f} (0 = no better than random)")
    chosen = targets.iloc[np.argsort(-s_targets)[: args.budget]][["customer_id"]]
    out = run_.folder / f"targets_{args.learner}.csv"
    chosen.to_csv(out, index=False)
    print(f"  Chose {len(chosen):,} of next month's {len(targets):,} customers: {out}. Check them: xp check")
    run_.save_analysis({"command": NAME, "learner": args.learner, "qini": q, "budget": args.budget,
                        "targets_file": str(out), "truth_file": str(run_.folder / run_.meta["tables"]["truth_targets"]["file"]),
                        "curve": {"shares": shares.tolist(), "gains": gains.tolist()}})


def check(analysis, truth):
    import pandas as pd

    tt = pd.read_csv(analysis["truth_file"]).set_index("customer_id")["true_uplift"]
    chosen = pd.read_csv(analysis["targets_file"])["customer_id"]
    got = float(tt.loc[chosen].sum())
    rand = float(tt.mean() * len(chosen))
    harmed = int((tt.loc[chosen] < 0).sum())
    best = float(tt.sort_values().iloc[-len(chosen):].sum())  # the budget's best list, from the true chances
    return [f"Your {len(chosen):,} customers: {got:+.0f} extra orders expected (from the simulator's true chances).",
            f"  Random {len(chosen):,}: {rand:+.0f}. The best possible {len(chosen):,}: {best:+.0f}. "
            f"Emailing all {truth['targets']['customers']:,}: {truth['targets']['expected_extra_orders_all']:+.0f}.",
            f"  {harmed:,} of your customers order less because of the email (do-not-disturbs)."]
