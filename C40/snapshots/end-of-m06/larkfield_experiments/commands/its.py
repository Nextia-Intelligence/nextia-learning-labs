"""xp its: interrupted time series on the launch run. One regression on the days around the launch: a trend, the
weekday, the shopping days around holidays and the sale, plus a step on the launch day. The step is the effect;
the rest of the model is the counterfactual (what the days after would have been without the block)."""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from ..runs import load_run

NAME = "its"
HELP = "interrupted time series on the launch run: the block's effect after the trend, season and holidays"


def add(p):
    p.add_argument("run", nargs="?", default="launch", help="a launch run (default: the newest launch run)")
    p.add_argument("--weeks", type=int, default=4, help="weeks after the launch to measure")
    p.add_argument("--before", type=int, default=8, help="weeks before the launch to learn the trend from")
    p.add_argument("--simple", action="store_true", help="the simple model: trend and weekday only")


def run(args):
    run_ = load_run(args.run)
    d = run_.table("daily")
    launch = pd.Timestamp(run_.meta["events"]["launch"])
    dates = pd.to_datetime(d["date"])
    d["t"] = (dates - dates.min()).dt.days
    d["post"] = (dates >= launch).astype(int)
    d["log_orders"] = np.log(d["orders"])
    d = d[(dates >= launch - pd.Timedelta(weeks=args.before)) & (dates < launch + pd.Timedelta(weeks=args.weeks))]
    terms = "t + C(weekday)" if args.simple else "t + C(weekday) + holiday_window + sale"
    m = smf.ols(f"log_orders ~ post + {terms}", data=d).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
    b, se = m.params["post"], m.bse["post"]
    est, low, high = np.expm1(b), np.expm1(b - 1.96 * se), np.expm1(b + 1.96 * se)
    model = "trend and weekday only" if args.simple else "trend, weekday, yearly season, holiday windows and the sale"
    print(f"Interrupted time series ({model}), {len(d)} days ({args.before} weeks before, {args.weeks} after), "
          f"launch {launch.date()}:")
    print(f"  Effect of the launch on daily orders: {est:+.1%} (95% interval {low:+.1%} to {high:+.1%}; "
          f"errors robust to 7 days of autocorrelation).")
    run_.save_analysis({"command": NAME, "simple": args.simple, "estimate": float(est), "low": float(low),
                        "high": float(high)})


def check(analysis, truth):
    t = truth["block_effect_on_orders"]
    inside = analysis["low"] <= t <= analysis["high"]
    return [f"True effect (from the simulator): {t:+.1%} on daily orders.",
            f"Your estimate: {analysis['estimate']:+.1%} ({analysis['low']:+.1%} to {analysis['high']:+.1%}): the "
            f"interval {'contains' if inside else 'does NOT contain'} it."]
