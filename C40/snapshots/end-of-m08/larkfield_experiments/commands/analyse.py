"""xp analyse: the effect of B against A in a randomised test, with its 95% interval."""

from ..cuped import cuped_adjust, variance_reduction
from ..metrics import RATIOS, metric_values, split
from ..runs import load_run
from ..stats import bootstrap_diff, describe, diff_means, diff_ratio

NAME = "analyse"
HELP = "the difference B − A of a metric, its 95% interval and p-value (with --cuped, --bootstrap, --by)"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--metric", help="the metric (default: the scenario's primary metric)")
    p.add_argument("--cuped", action="store_true", help="adjust with the spending before the test (pre_spend)")
    p.add_argument("--bootstrap", type=int, metavar="N", help="a bootstrap interval with N resamples")
    p.add_argument("--by", help="also show the effect in each segment of this column, e.g. device")
    p.add_argument("--table", help="the table whose rows are the units (default: customers, or the scenario's own)")


def estimate(df, metric, cuped=False, bootstrap=None):
    a, b = split(df)
    if metric in RATIOS:
        num, den = RATIOS[metric]
        a, b = a[a[den] > 0], b[b[den] > 0]
        return diff_ratio(a[num], a[den], b[num], b[den])
    ya, yb = metric_values(a, metric), metric_values(b, metric)
    extra = {}
    if cuped:
        both = metric_values(df, metric)
        adj, theta = cuped_adjust(both, df["pre_spend"])
        ya, yb = adj[(df["variant"] == "A").to_numpy()], adj[(df["variant"] == "B").to_numpy()]
        extra = {"cuped_theta": theta, "variance_removed": variance_reduction(both, df["pre_spend"])}
    r = bootstrap_diff(ya, yb, bootstrap) if bootstrap else diff_means(ya, yb)
    if cuped:
        r["method"] += ", CUPED"
    return {**r, **extra}


def run(args):
    run_ = load_run(args.run)
    meta = run_.meta
    table = args.table or meta.get("analysis_table", "customers")
    df = run_.table(table)
    metric = args.metric or meta.get("primary_metric")
    r = estimate(df, metric, args.cuped, args.bootstrap)
    print(f"Run {run_.folder.name} (synthetic): {meta['about']}.")
    units = {"customers": "customers", "visits": "sessions", "days": "days"}.get(table, "rows")
    print(f"Metric: {metric}. A: {r['n_a']:,} {units}, mean {r['mean_a']:.4f}. "
          f"B: {r['n_b']:,} {units}, mean {r['mean_b']:.4f}.")
    print("  " + describe(r, digits=4))
    if args.cuped:
        print(f"  CUPED removed {r['variance_removed']:.1%} of the variance (theta {r['cuped_theta']:.3f}).")
    segments = {}
    if args.by:
        for value, part in df.groupby(args.by):
            s = estimate(part, metric, args.cuped)
            segments[str(value)] = s
            print(f"  {args.by} = {value}: " + describe(s, digits=4))
    result = {"command": NAME, "metric": metric, "table": table, **r, "segments": segments}
    path = run_.save_analysis(result)
    print(f"Saved to {path}. Compare with the true effect: xp check")


def check(analysis, truth):
    """Lines that compare the saved estimate with the simulator's true effect."""
    t = truth.get(analysis["metric"])
    if not t or "effect" not in t:
        return [f"The simulator has no true effect for the metric '{analysis['metric']}' in this scenario."]
    eff = t["effect"]
    inside = analysis["low"] <= eff <= analysis["high"]
    return [f"True effect (from the simulator): {eff:+.4f} {t.get('unit', '')}.",
            f"Your estimate: {analysis['difference']:+.4f}, 95% interval {analysis['low']:+.4f} to "
            f"{analysis['high']:+.4f}: the interval {'contains' if inside else 'does NOT contain'} the true effect."]
