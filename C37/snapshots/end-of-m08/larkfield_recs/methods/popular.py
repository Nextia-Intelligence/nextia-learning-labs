"""Non-personal baselines: everyone gets the same list (or the same list for their favourite categories)."""

import numpy as np

from . import Method, top_k


def popularity(period, days=None):
    """How many different customers ordered each product (in the last `days` days before the period, or ever)."""
    tr = period.train
    o = tr[tr.event == "order"]
    if days:
        o = o[o.day >= period.start_day - days]
    pairs = o[["c", "p"]].drop_duplicates()
    return np.bincount(pairs.p.to_numpy(), minlength=period.shop.n_products).astype(float)


def popular_list(period, days=None, n=200):
    s = popularity(period, days)
    s[~period.available] = -np.inf
    order = np.argsort(-s, kind="stable")
    return order[np.isfinite(s[order]) & (s[order] > 0)][:n]


class Popular(Method):
    """The most ordered products: over the whole training log, or over its last `days` days (trending)."""

    def fit(self):
        self.score = popularity(self.period, self.settings.get("days"))
        return self

    def scores(self, users):
        return np.tile(self.score, (len(users), 1))

    def recommend(self, users, k=10):
        row = top_k(self.score[None, :], k, self.period.available)[0]
        return np.tile(row, (len(users), 1))


class Random(Method):
    """Random products on sale: the floor that every method must beat."""

    def recommend(self, users, k=10):
        rng = np.random.default_rng(self.settings.get("seed", 37))
        pool = np.flatnonzero(self.period.available)
        return np.array([rng.choice(pool, k, replace=False) for _ in users])


METHODS = {
    "popular": (Popular, {}, "the most ordered products over the whole training log"),
    "random": (Random, {}, "random products on sale"),
}
