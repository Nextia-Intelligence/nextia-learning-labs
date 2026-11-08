"""A randomised A/B test in the simulator: customers get version A or B by a coin flip on their first visit."""

import numpy as np

from .world import TEST_START, Effect, make_population, per_customer, simulate_test, truth_of


def ab_run(seed: int, n: int, days: int, effect, start=TEST_START, lose=None, share_b: float = 0.5,
           potentials=False):
    """Runs one test. Returns the tables a real test has (customers, visits) and the truth.

    lose (planted problems only): lose(pop, variant, rng) returns a function that marks visits the log loses."""
    rng = np.random.default_rng(seed)
    pop = make_population(n, rng)
    variant = (rng.random(n) < share_b).astype(int)  # the coin flip
    visits, outcomes = simulate_test(pop, rng, days, start, variant, effect,
                                     lose=lose(pop, variant, rng) if lose else None,
                                     potentials=potentials)
    hidden = [c for c in visits.columns if c.startswith("_")]
    customers = per_customer(visits, outcomes)
    tables = {"customers": customers, "visits": visits.drop(columns=hidden)}
    return tables, truth_of(outcomes), (outcomes, visits[hidden + ["date", "customer_id"]] if hidden else None)


def no_effect(idx, day, since):
    return Effect()
