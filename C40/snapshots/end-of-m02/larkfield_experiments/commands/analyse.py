"""xp analyse: the effect of B against A in a randomised test, with its 95% interval."""

from ..metrics import RATIOS, metric_values, split
from ..runs import load_run
from ..stats import describe, diff_means, diff_ratio

NAME = "analyse"
HELP = "the difference B − A of a metric, its 95% interval and p-value"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--metric", help="the metric (default: the scenario's primary metric)")


def estimate(df, metric):
    a, b = split(df)
    if metric in RATIOS:
        num, den = RATIOS[metric]
        a, b = a[a[den] > 0], b[b[den] > 0]
        return diff_ratio(a[num], a[den], b[num], b[den])
    return diff_means(metric_values(a, metric), metric_values(b, metric))


def run(args):
    run_ = load_run(args.run)
    meta = run_.meta
    df = run_.table("customers")
    metric = args.metric or meta.get("primary_metric")
    r = estimate(df, metric)
    print(f"Run {run_.folder.name} (synthetic): {meta['about']}.")
    print(f"Metric: {metric}. A: {r['n_a']:,} customers, mean {r['mean_a']:.4f}. "
          f"B: {r['n_b']:,} customers, mean {r['mean_b']:.4f}.")
    print("  " + describe(r, digits=4))
    result = {"command": NAME, "metric": metric, "table": "customers", **r}
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
