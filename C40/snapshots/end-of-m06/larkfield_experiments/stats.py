"""The statistics of an A/B test: a difference, its 95% interval and its p-value.

The mathematics course explains each formula. Every function returns a dict, so the commands can print it and
save it.
"""

import numpy as np
from scipy import stats

Z95 = 1.959963984540054


def diff_means(a, b, level=0.95) -> dict:
    """Difference of means (B − A) with Welch's t-test. Works for 0/1 values (proportions) too."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
    t = stats.t.ppf(0.5 + level / 2, df)
    d = mb - ma
    p = 2 * stats.t.sf(abs(d / se), df) if se > 0 else 1.0
    return {"n_a": len(a), "n_b": len(b), "mean_a": float(ma), "mean_b": float(mb), "difference": float(d),
            "relative": float(d / ma) if ma else None, "se": float(se), "low": float(d - t * se),
            "high": float(d + t * se), "p": float(p), "method": "Welch t-test"}


def diff_ratio(num_a, den_a, num_b, den_b) -> dict:
    """Difference of two ratio metrics, such as returns per order (sum of returns / sum of orders), B − A.

    The customers are the units, so the ratio's standard error comes from the delta method."""
    def ratio_and_var(num, den):
        num, den = np.asarray(num, float), np.asarray(den, float)
        n, mx, my = len(num), num.mean(), den.mean()
        r = mx / my
        cov = np.cov(num, den, ddof=1)
        var = (cov[0, 0] - 2 * r * cov[0, 1] + r**2 * cov[1, 1]) / (my**2 * n)
        return r, var, n
    ra, va, na = ratio_and_var(num_a, den_a)
    rb, vb, nb = ratio_and_var(num_b, den_b)
    d, se = rb - ra, np.sqrt(va + vb)
    p = 2 * stats.norm.sf(abs(d / se))
    return {"n_a": na, "n_b": nb, "mean_a": float(ra), "mean_b": float(rb), "difference": float(d),
            "relative": float(d / ra), "se": float(se), "low": float(d - Z95 * se), "high": float(d + Z95 * se),
            "p": float(p), "method": "ratio, delta method"}


def bootstrap_diff(a, b, n_boot=2000, seed=0) -> dict:
    """Percentile bootstrap interval of the difference of means (B − A): resample each group with replacement."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        diffs[i] = b[rng.integers(0, len(b), len(b))].mean() - a[rng.integers(0, len(a), len(a))].mean()
    d = b.mean() - a.mean()
    low, high = np.percentile(diffs, [2.5, 97.5])
    p = min(1.0, 2 * min((diffs <= 0).mean(), (diffs >= 0).mean()))
    return {"n_a": len(a), "n_b": len(b), "mean_a": float(a.mean()), "mean_b": float(b.mean()), "difference": float(d),
            "relative": float(d / a.mean()) if a.mean() else None, "se": float(diffs.std(ddof=1)),
            "low": float(low), "high": float(high), "p": float(p), "method": f"bootstrap ({n_boot} resamples)"}


def describe(r: dict, unit: str = "", digits: int = 3) -> str:
    """One line: the difference, the relative change, the 95% interval and the p-value."""
    f = f"{{:+.{digits}f}}"
    rel = f" ({r['relative']:+.1%})" if r.get("relative") is not None else ""
    unit = f" {unit}" if unit else ""
    return (f"difference {f.format(r['difference'])}{rel}{unit}, 95% interval {f.format(r['low'])} to "
            f"{f.format(r['high'])}, p = {r['p']:.3g} ({r['method']})")
