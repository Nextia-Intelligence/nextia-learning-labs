"""xp rdd: regression discontinuity at the Gold tier's threshold. Fit a line on each side within a bandwidth and
read the jump at the threshold. --donut leaves out the customers closest to the threshold."""

import statsmodels.formula.api as smf
from scipy.stats import binomtest

from ..runs import load_run

NAME = "rdd"
HELP = "regression discontinuity on the loyalty run: the jump at 500 dollars, with a density check"


def add(p):
    p.add_argument("run", nargs="?", default="loyalty", help="a loyalty run (default: the newest loyalty run)")
    p.add_argument("--bandwidth", type=float, default=100, help="dollars on each side of the threshold")
    p.add_argument("--donut", type=float, default=0, help="leave out customers this close above the threshold")


def jump(df, x, y, c, h, donut=0):
    d = df[(df[x] >= c - h) & (df[x] < c + h)].copy()
    if donut:
        d = d[(d[x] < c) | (d[x] >= c + donut)]
    d["xc"], d["above"] = d[x] - c, (d[x] >= c).astype(int)
    m = smf.ols(f"{y} ~ above * xc", data=d).fit(cov_type="HC1")
    b, se = m.params["above"], m.bse["above"]
    return {"estimate": float(b), "low": float(b - 1.96 * se), "high": float(b + 1.96 * se), "n": len(d)}


def run(args):
    run_ = load_run(args.run)
    df = run_.table("customers")
    x, y, c = run_.meta["running_variable"], run_.meta["outcome"], run_.meta["threshold"]
    print(f"Regression discontinuity at {x} = {c:g}, outcome {y}.")
    below, above = int(((df[x] >= c - 20) & (df[x] < c)).sum()), int(((df[x] >= c) & (df[x] < c + 20)).sum())
    p = binomtest(above, below + above, 0.5).pvalue
    print(f"  Density check: {below} customers in the 20 dollars below, {above} in the 20 above (p = {p:.3g}). "
          f"{'Bunching above the threshold: people may game it.' if p < 0.01 else 'No sign of bunching.'}")
    r = jump(df, x, y, c, args.bandwidth, args.donut)
    print(f"  Bandwidth {args.bandwidth:g}{f', donut {args.donut:g}' if args.donut else ''}: jump {r['estimate']:+.2f} "
          f"dollars (95% interval {r['low']:+.2f} to {r['high']:+.2f}), {r['n']:,} customers.")
    for h in (50, 100, 150, 200, 300):
        s = jump(df, x, y, c, h, args.donut)
        print(f"    bandwidth {h:>3}: {s['estimate']:+7.2f} ({s['low']:+.2f} to {s['high']:+.2f}), {s['n']:,} customers")
    naive = df.loc[df[x] >= c, y].mean() - df.loc[df[x] < c, y].mean()
    print(f"  Naive (all Gold against all others): {naive:+.2f} dollars.")
    run_.save_analysis({"command": NAME, "bandwidth": args.bandwidth, "donut": args.donut, **r,
                        "density_p": float(p), "naive": float(naive)})


def check(analysis, truth):
    t = truth["effect"]["at_threshold"]
    inside = analysis["low"] <= t <= analysis["high"]
    return [f"True effect at the threshold (from the simulator): {t:+.2f} dollars.",
            f"Your estimate: {analysis['estimate']:+.2f} ({analysis['low']:+.2f} to {analysis['high']:+.2f}): the "
            f"interval {'contains' if inside else 'does NOT contain'} it. Naive answer: {analysis['naive']:+.2f}.",
            f"Planted: {truth['planted']}"]
