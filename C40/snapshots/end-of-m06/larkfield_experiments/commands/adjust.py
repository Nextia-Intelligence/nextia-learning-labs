"""xp adjust: estimate the block's effect from the logs (no test) by regression, matching and weighting."""

import numpy as np

from ..adjust import CONFOUNDERS, ipw, match, prepare, propensity, regression, smd
from ..runs import load_run

NAME = "adjust"
HELP = "regression, propensity-score matching and weighting on the logs run, with a balance check"


def add(p):
    p.add_argument("run", nargs="?", default="logs", help="a logs run (default: the newest logs run)")
    p.add_argument("--covariates", default=",".join(CONFOUNDERS),
                   help=f"comma-separated confounders (default: {','.join(CONFOUNDERS)})")
    p.add_argument("--add", default="", help="extra columns to add by mistake, e.g. pages_viewed (a mediator)")


def run(args):
    run_ = load_run(args.run)
    d = prepare(run_.table("customers"))
    cov = [c for c in args.covariates.split(",") if c] + [c for c in args.add.split(",") if c]
    treatment, outcome = "used_block", "revenue"
    naive = d.loc[d[treatment] == 1, outcome].mean() - d.loc[d[treatment] == 0, outcome].mean()
    print(f"Run {run_.folder.name}: effect of {treatment} on {outcome} (dollars per customer, 28 days).")
    print(f"  Covariates: {', '.join(cov)}")
    print(f"  {'naive (users − non-users)':<32} {naive:+7.2f}")
    ps = propensity(d, treatment, cov)
    results = [regression(d, treatment, outcome, cov), match(d, treatment, outcome, ps), ipw(d, treatment, outcome, ps)]
    for r in results:
        print(f"  {r['method']:<32} {r['estimate']:+7.2f}  (95% interval {r['low']:+.2f} to {r['high']:+.2f}; {r['target']})")
    t = d[treatment].to_numpy() == 1
    print(f"  Overlap: propensity scores {ps[t].min():.3f}–{ps[t].max():.3f} (users), "
          f"{ps[~t].min():.3f}–{ps[~t].max():.3f} (non-users).")
    w = np.where(t, 1 / ps, 1 / (1 - ps))
    before, after = smd(d, treatment, cov), smd(d, treatment, cov, w)
    print("  Balance (standardised mean difference; below 0.1 is good): " + ", ".join(
        f"{c} {before[c]:+.2f} → {after[c]:+.2f}" for c in cov))
    run_.save_analysis({"command": NAME, "covariates": cov, "naive": float(naive), "results": results,
                        "balance_before": before, "balance_after": after})


def check(analysis, truth):
    lines = [f"True effect (from the simulator): ATE {truth['ate']['effect']:+.2f}, ATT {truth['att']['effect']:+.2f} "
             f"dollars per customer. Naive: {analysis['naive']:+.2f}."]
    for r in analysis["results"]:
        t = truth[r["target"].lower()]["effect"]
        inside = r["low"] <= t <= r["high"]
        lines.append(f"  {r['method']}: {r['estimate']:+.2f} against {r['target']} {t:+.2f}: the interval "
                     f"{'contains' if inside else 'does NOT contain'} it.")
    lines.append(f"Hidden from the log: {truth['hidden_confounder']}")
    return lines
