"""Small statistics for the monitors, with Python's standard library only.

- PSI (population stability index): how much a distribution moved, bin by bin:
      PSI = sum over bins of (current% - reference%) x ln(current% / reference%)
  A common rule of thumb (not a law): below 0.1 no real change, 0.1 to 0.2 a small change,
  above 0.2 a large change. Empty bins get a tiny share (0.0001) so the logarithm exists.
- chi-square test of homogeneity: are two samples of categories from the same distribution?
  The p-value is the chance of a difference at least this large if nothing changed. We call
  p < 0.01 "different". With thousands of tickets, even a tiny change gets a small p-value:
  read the PSI (how much) next to the p-value (how sure).
- Wilson interval: a 95% interval for a share measured on n items (n can be small).
"""

import math
from collections import Counter

EPS = 1e-4


def shares(counts: Counter, keys) -> list[float]:
    total = sum(counts.values()) or 1
    return [max(counts.get(k, 0) / total, EPS) for k in keys]


def psi(reference: Counter, current: Counter) -> float:
    keys = sorted(set(reference) | set(current), key=str)
    r, c = shares(reference, keys), shares(current, keys)
    return sum((ci - ri) * math.log(ci / ri) for ri, ci in zip(r, c, strict=True))


def quantile_edges(values: list[float], bins: int = 10) -> list[float]:
    """Bin edges at the reference's deciles (the same edges are used for the current data)."""
    ordered = sorted(values)
    edges = []
    for i in range(1, bins):
        x = ordered[min(len(ordered) - 1, int(i * len(ordered) / bins))]
        if not edges or x > edges[-1]:
            edges.append(x)
    return edges


def binned(values: list[float], edges: list[float]) -> Counter:
    out: Counter = Counter()
    for v in values:
        out[sum(v > e for e in edges)] += 1
    return out


def chi_square(reference: Counter, current: Counter) -> tuple[float, int, float]:
    """(statistic, degrees of freedom, p-value) for a 2 x k table of counts."""
    keys = [k for k in set(reference) | set(current) if reference.get(k, 0) + current.get(k, 0) > 0]
    n1, n2 = sum(reference[k] for k in keys), sum(current[k] for k in keys)
    if len(keys) < 2 or not n1 or not n2:
        return 0.0, 0, 1.0
    stat = 0.0
    for k in keys:
        col = reference[k] + current[k]
        for observed, n in ((reference[k], n1), (current[k], n2)):
            expected = col * n / (n1 + n2)
            stat += (observed - expected) ** 2 / expected
    df = len(keys) - 1
    return stat, df, upper_gamma_q(df / 2, stat / 2)


def upper_gamma_q(a: float, x: float) -> float:
    """The regularized upper incomplete gamma function Q(a, x) (series or continued fraction)."""
    if x <= 0:
        return 1.0
    lg = math.lgamma(a)
    if x < a + 1:  # series for P, then Q = 1 - P
        term = total = 1.0 / a
        n = a
        for _ in range(1000):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return max(0.0, 1.0 - total * math.exp(-x + a * math.log(x) - lg))
    b, c, d = x + 1 - a, 1e300, 1.0 / (x + 1 - a)  # continued fraction (Lentz)
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - lg) * h


def wilson(good: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = good / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def reviews_needed(share: float, margin: float, z: float = 1.96) -> int:
    """Reviews needed so that a measured share has about this margin (95%)."""
    return math.ceil(z * z * share * (1 - share) / (margin * margin))
