"""A multi-armed bandit with Thompson sampling, against a fixed equal split (an A/B/n test).

Thompson sampling in plain words: keep, for each option, a range of believable click rates (a Beta distribution
from its clicks and non-clicks). For each visitor, draw one believable rate per option and show the option with
the highest draw. Options that look good get more traffic; options we know little about still get some.
"""

import numpy as np


def run_bandit(rates, visitors, rng, policy="thompson", batch=100):
    """Returns (shown per option, clicks per option, the share of traffic each option got in each tenth)."""
    k = len(rates)
    clicks, shown = np.zeros(k), np.zeros(k)
    history = []
    for start in range(0, visitors, batch):
        m = min(batch, visitors - start)
        if policy == "thompson":
            draws = rng.beta(1 + clicks[:, None], 1 + shown[:, None] - clicks[:, None], (k, m))
            arm = draws.argmax(axis=0)
        else:
            arm = rng.integers(0, k, m)
        got = rng.random(m) < np.asarray(rates)[arm]
        np.add.at(shown, arm, 1)
        np.add.at(clicks, arm, got)
        history.append(np.bincount(arm, minlength=k))
    h = np.array(history)
    tenths = np.array_split(h, 10)
    shares = [t.sum(axis=0) / t.sum() for t in tenths]
    return shown, clicks, np.array(shares)


def prob_best(shown, clicks, rng, draws=4000):
    s = rng.beta(1 + clicks[:, None], 1 + shown[:, None] - clicks[:, None], (len(shown), draws))
    return np.bincount(s.argmax(axis=0), minlength=len(shown)) / draws
