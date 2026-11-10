"""Sample size and power: how many customers a test needs to find an effect of a given size.

statsmodels does the formula; `simulated_power` checks it by running the simulator many times.
"""

import math

import numpy as np
from statsmodels.stats.power import NormalIndPower, TTestIndPower
from statsmodels.stats.proportion import proportion_effectsize


def sample_size(baseline, mde, sd=None, power=0.8, alpha=0.05) -> int:
    """Customers per group. baseline: the control mean (a proportion if sd is None); mde: the smallest effect
    worth finding, in the metric's own unit (0.01 = one percentage point for a proportion)."""
    if sd is None:
        es = abs(proportion_effectsize(baseline + mde, baseline))
        n = NormalIndPower().solve_power(effect_size=es, power=power, alpha=alpha, ratio=1.0)
    else:
        n = TTestIndPower().solve_power(effect_size=abs(mde) / sd, power=power, alpha=alpha, ratio=1.0)
    return math.ceil(n)


def power_of(n_per_group, baseline, mde, sd=None, alpha=0.05) -> float:
    if sd is None:
        es = abs(proportion_effectsize(baseline + mde, baseline))
        return float(NormalIndPower().power(effect_size=es, nobs1=n_per_group, alpha=alpha, ratio=1.0))
    return float(TTestIndPower().power(effect_size=abs(mde) / sd, nobs1=n_per_group, alpha=alpha, ratio=1.0))


def simulated_power(run_test, runs=200, alpha=0.05, seed0=1000) -> float:
    """The share of simulated tests whose p-value is below alpha. run_test(seed) returns a p-value."""
    p = np.array([run_test(seed0 + i) for i in range(runs)])
    return float((p < alpha).mean())
