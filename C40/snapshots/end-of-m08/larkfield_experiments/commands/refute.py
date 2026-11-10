"""xp refute: try to break your own estimate with DoWhy's refutation tests, and ask how strong a hidden
confounder would need to be to change the answer."""

import warnings

from ..adjust import CONFOUNDERS, prepare
from ..runs import load_run

NAME = "refute"
HELP = "DoWhy refutation tests (placebo treatment, random common cause, data subsets) and a hidden-confounder grid"


def add(p):
    p.add_argument("run", nargs="?", default="logs", help="a logs run (default: the newest logs run)")
    p.add_argument("--simulations", type=int, default=20, help="repeats of each refutation test")


def run(args):
    warnings.filterwarnings("ignore")
    from dowhy import CausalModel

    run_ = load_run(args.run)
    d = prepare(run_.table("customers"))
    d["used_block"] = d["used_block"].astype(bool)
    cols = CONFOUNDERS + ["used_block", "revenue"]
    model = CausalModel(data=d[cols], treatment="used_block", outcome="revenue", common_causes=CONFOUNDERS)
    estimand = model.identify_effect(proceed_when_unidentifiable=True)
    est = model.estimate_effect(estimand, method_name="backdoor.linear_regression")
    print(f"DoWhy estimate (backdoor adjustment, linear regression): {est.value:+.2f} dollars per customer.")
    out = {"command": NAME, "estimate": float(est.value), "refuters": {}}
    for name, kw in (("placebo_treatment_refuter", {"placebo_type": "permute"}),
                     ("random_common_cause", {}), ("data_subset_refuter", {"subset_fraction": 0.8})):
        r = model.refute_estimate(estimand, est, method_name=name, num_simulations=args.simulations,
                                  random_seed=1, n_jobs=1, **kw)
        p = r.refutation_result.get("p_value") if isinstance(r.refutation_result, dict) else None
        print(f"  {name:<27} new effect {r.new_effect:+.2f}" + (f" (p = {p:.2f})" if p is not None else ""))
        out["refuters"][name] = {"new_effect": float(r.new_effect), "p": None if p is None else float(p)}
    print("  Expected: the placebo gives about 0; the other two stay close to the estimate. Passing does not prove "
          "the estimate: these tests cannot see a confounder that is missing from the data.")
    print("Hidden confounder: how big must it be to move the estimate to 0? (a 0/1 cause; its share among users "
          "minus non-users × its effect on revenue in dollars)")
    grid = {}
    for share_gap in (0.05, 0.10, 0.20, 0.30):
        row = []
        for dollars in (5, 10, 20, 40):
            left = est.value - share_gap * dollars
            row.append(f"{left:+6.2f}")
            grid[f"{share_gap}x{dollars}"] = float(left)
        print(f"  share gap {share_gap:.2f}: " + "  ".join(f"{d:>2} $ → {v}" for d, v in zip((5, 10, 20, 40), row)))
    out["grid"] = grid
    run_.save_analysis(out)


def check(analysis, truth):
    return [f"True effect (from the simulator): ATE {truth['ate']['effect']:+.2f} dollars per customer; your DoWhy "
            f"estimate {analysis['estimate']:+.2f}.",
            f"The refutation tests passed or failed without knowing this: {truth['hidden_confounder']}"]
