"""Ranking metrics for suggestion lists, per customer, and a bootstrap interval over customers.

A list is an array of product numbers (-1 = an empty place). `truth` is the set of products the customer really
ordered in the period. Relevance is binary: a suggestion is right when the customer ordered that product.
"""

import numpy as np


def hits(rec, truth):
    """1 where the suggestion at that place was ordered, else 0."""
    t = {int(x) for x in truth}
    return np.array([1.0 if int(r) in t else 0.0 for r in rec])


def precision_at_k(rec, truth, k=10):
    return hits(rec[:k], truth).sum() / k


def recall_at_k(rec, truth, k=10):
    return hits(rec[:k], truth).sum() / len(truth) if len(truth) else 0.0


def hit_at_k(rec, truth, k=10):
    return float(hits(rec[:k], truth).any())


def average_precision_at_k(rec, truth, k=10):
    """Mean of the precision at each right place, divided by min(number ordered, k)."""
    h = hits(rec[:k], truth)
    if not h.any():
        return 0.0
    prec = np.cumsum(h) / np.arange(1, len(h) + 1)
    return float((prec * h).sum() / min(len(truth), k))


def ndcg_at_k(rec, truth, k=10):
    """DCG of the list divided by the best possible DCG; discount log2(place + 1)."""
    h = hits(rec[:k], truth)
    disc = 1.0 / np.log2(np.arange(2, len(h) + 2))
    ideal = disc[: min(len(truth), k)].sum()
    return float((h * disc).sum() / ideal) if ideal else 0.0


PER_CUSTOMER = {"precision": precision_at_k, "recall": recall_at_k, "hit": hit_at_k, "map": average_precision_at_k,
                "ndcg": ndcg_at_k}


def per_customer(recs, truth, k=10, names=("recall", "ndcg")):
    """{metric: array with one value per customer}."""
    return {n: np.array([PER_CUSTOMER[n](r, t, k) for r, t in zip(recs, truth)]) for n in names}


def coverage(recs, available, k=10):
    """Share of the products on sale that appear in at least one list."""
    shown = np.unique(recs[:, :k][recs[:, :k] >= 0])
    return float(np.isin(shown, np.flatnonzero(available)).sum() / available.sum())


def bootstrap(values, n=1000, seed=37):
    """Mean and 95% interval: resample customers with replacement n times."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), (n, len(values)))].mean(axis=1)
    return float(values.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_difference(a, b, n=1000, seed=37):
    """Mean of b - a per customer with a 95% bootstrap interval (the same customers in both)."""
    return bootstrap(np.asarray(b) - np.asarray(a), n, seed)
