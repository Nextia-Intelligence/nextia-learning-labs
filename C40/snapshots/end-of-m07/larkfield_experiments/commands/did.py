"""xp did: difference-in-differences. Quebec's change from before to after, minus the change of the comparison
areas, as a regression with area and week effects and errors clustered by area."""

import numpy as np
import statsmodels.formula.api as smf

from ..runs import load_run

NAME = "did"
HELP = "difference-in-differences on the regions run: treated province against --control provinces"


def add(p):
    p.add_argument("run", nargs="?", default="regions", help="a regions run (default: the newest regions run)")
    p.add_argument("--control", default="ON", help="comma-separated provinces, or 'all' (default: ON)")
    p.add_argument("--placebo", action="store_true",
                   help="also a placebo test: pretend the change started 26 weeks earlier, on the weeks before it")


def did(df, treated, controls, start):
    d = df[df.province.isin([treated, *controls])].copy()
    d["treated"] = (d.province == treated).astype(int)
    d["post"] = (d.week >= start).astype(int)
    d["log_revenue"] = np.log(d.revenue)
    m = smf.ols("log_revenue ~ treated:post + C(area) + C(week)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["area"].astype("category").cat.codes})
    b, se = m.params["treated:post"], m.bse["treated:post"]
    return {"estimate": float(np.expm1(b)), "low": float(np.expm1(b - 1.96 * se)), "high": float(np.expm1(b + 1.96 * se)),
            "p": float(m.pvalues["treated:post"]), "areas": int(d.area.nunique())}


def run(args):
    run_ = load_run(args.run)
    df = run_.table("areas_weekly")
    treated, start = run_.meta["events"]["treated"], run_.meta["events"]["rollout"]
    provinces = sorted(df.province.unique())
    controls = [p for p in provinces if p != treated] if args.control == "all" else args.control.split(",")
    r = did(df, treated, controls, start)
    print(f"Difference-in-differences: {treated} against {', '.join(controls)} ({r['areas']} areas), change on {start}.")
    pre = df[df.week < start].assign(group=lambda x: np.where(x.province == treated, "treated", "control"))
    pre = pre[pre.province.isin([treated, *controls])]
    trend = pre.groupby(["group", "week"]).revenue.sum().groupby("group").apply(
        lambda s: np.polyfit(np.arange(len(s)), np.log(s.values), 1)[0])
    print(f"  Effect on weekly sales: {r['estimate']:+.1%} (95% interval {r['low']:+.1%} to {r['high']:+.1%}, "
          f"p = {r['p']:.3g}; errors clustered by area).")
    print(f"  Parallel trends before the change: weekly growth {trend['treated']:+.3%} (treated) against "
          f"{trend['control']:+.3%} (control).")
    result = {"command": NAME, "controls": controls, **r, "pre_trend_gap": float(trend["treated"] - trend["control"])}
    if args.placebo:
        fake_start = str(np.datetime64(start) - np.timedelta64(26 * 7, "D"))
        pl = did(df[df.week < start], treated, controls, fake_start)
        print(f"  Placebo (a fake change on {fake_start}, weeks before the real one only): {pl['estimate']:+.1%} "
              f"({pl['low']:+.1%} to {pl['high']:+.1%}, p = {pl['p']:.3g}). A clear placebo effect means the trends "
              f"were not parallel.")
        result["placebo"] = pl
    run_.save_analysis(result)


def check(analysis, truth):
    t = truth["effect"]["relative"]
    inside = analysis["low"] <= t <= analysis["high"]
    return [f"True effect (from the simulator): {t:+.1%} on Quebec's weekly sales.",
            f"Your estimate: {analysis['estimate']:+.1%} ({analysis['low']:+.1%} to {analysis['high']:+.1%}), "
            f"{100 * (analysis['estimate'] - t):+.1f} percentage points from the truth; the interval {'contains' if inside else 'does NOT contain'} it."]
