"""Recommendation methods. A method gets a Period, learns from period.train in fit(), and returns lists of
product numbers in recommend(users, k). Shared helpers are here."""

import numpy as np


class Method:
    """The interface: fit(), then recommend(users, k) -> array (customers × k) of product numbers, -1 = empty."""

    def __init__(self, period, **settings):
        self.period = period
        self.shop = period.shop
        self.settings = settings

    def fit(self):
        return self

    def scores(self, users):
        raise NotImplementedError

    def recommend(self, users, k=10):
        return top_k(self.scores(users), k, self.period.available)


def top_k(scores, k, allowed=None):
    """The k best products per row; products not allowed (or with score -inf) are never chosen."""
    s = np.array(scores, dtype=np.float64, copy=True)
    if allowed is not None:
        s[:, ~allowed] = -np.inf
    k = min(k, s.shape[1])
    part = np.argpartition(-s, k - 1, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(s, part, axis=1), axis=1, kind="stable")
    out = np.take_along_axis(part, order, axis=1)
    out[np.take_along_axis(s, out, axis=1) == -np.inf] = -1
    return out


def fill(recs, fallback):
    """Fill the empty places (-1) of each list with the fallback list, skipping products already in the list."""
    recs = recs.copy()
    for row in recs:
        empty = np.flatnonzero(row < 0)
        if len(empty):
            have = set(row[row >= 0].tolist())
            extra = [p for p in fallback if p not in have][: len(empty)]
            row[empty[: len(extra)]] = extra
    return recs
