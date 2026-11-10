"""Hybrids: combine methods that are good for different customers and products.

- hybrid-blend: a weighted sum of ALS, content and trending scores, each scaled 0..1 for each customer.
- hybrid-switch: one method per segment (no history -> trending; little history -> content; else ALS).
- als+new: ALS, with `slots` places (from place `at`) kept for the new products closest to the customer's taste
  (content), so that new products are shown from their first day.
"""

import numpy as np

from . import Method, fill, top_k
from .content import Content
from .mf import Factorisation
from .popular import popular_list, popularity


def scale(s):
    """Each row scaled to 0..1; a row with no score (a customer with no history) becomes all 0."""
    s = np.where(np.isfinite(s), s, np.nan)
    ok = ~np.isnan(s).all(axis=1)
    out = np.zeros_like(s, dtype=float)
    if ok.any():
        lo, hi = np.nanmin(s[ok], axis=1, keepdims=True), np.nanmax(s[ok], axis=1, keepdims=True)
        out[ok] = np.nan_to_num((s[ok] - lo) / np.where(hi > lo, hi - lo, 1), nan=0.0)
    return out


class Blend(Method):
    def fit(self):
        self.als = Factorisation(self.period, algo="als").fit()
        self.content = Content(self.period).fit()
        self.trend = popularity(self.period, 28)
        self.fallback = popular_list(self.period, days=28)
        return self

    def scores(self, users):
        s = self.settings
        t = np.log1p(np.tile(self.trend, (len(users), 1)))
        return (s.get("w_als", 1.0) * scale(self.als.scores(users)) + s.get("w_content", 0.5) * scale(self.content.scores(users))
                + s.get("w_trending", 0.5) * scale(t))

    def recommend(self, users, k=10):
        return fill(top_k(self.scores(users), k, self.period.available), self.fallback)


class Switch(Method):
    def fit(self):
        self.als = Factorisation(self.period, algo="als").fit()
        self.content = Content(self.period).fit()
        self.fallback = popular_list(self.period, days=28)
        tr = self.period.train
        self.events = np.bincount(tr.c.to_numpy(), minlength=self.shop.n_customers)
        return self

    def recommend(self, users, k=10):
        out = np.tile(self.fallback[:k], (len(users), 1))
        n = self.events[users]
        few = (n > 0) & (n < self.settings.get("min_events", 5))
        many = n >= self.settings.get("min_events", 5)
        if few.any():
            out[few] = self.content.recommend(users[few], k)
        if many.any():
            out[many] = self.als.recommend(users[many], k)
        return out


class WithNewSlots(Method):
    def fit(self):
        self.base = Factorisation(self.period, algo="als").fit()
        self.content = Content(self.period).fit()
        days = self.settings.get("new_days", 30)
        self.new = self.period.available & (self.shop.added_day > self.period.start_day - days)
        self.fallback = popular_list(self.period, days=28)
        return self

    def recommend(self, users, k=10):
        slots, at = self.settings.get("slots", 2), self.settings.get("at", 4)
        base = self.base.recommend(users, k)
        if slots == 0 or not self.new.any():
            return base
        cs = self.content.scores(users)
        no_hist = ~np.isfinite(cs).any(axis=1)
        cs[no_hist] = self.content.emb @ self.content.emb[self.fallback[:20]].mean(axis=0)   # no history: near bestsellers
        new = top_k(cs, slots, self.new)
        out = np.empty_like(base)
        for i in range(len(users)):
            extra = [p for p in new[i] if p >= 0]
            rest = [p for p in base[i] if p not in extra]
            row = rest[: at - 1] + extra + rest[at - 1:]
            out[i] = row[:k]
        return out


METHODS = {
    "hybrid-blend": (Blend, {}, "ALS + 0.5 content + 0.5 trending, each scaled 0..1 per customer"),
    "hybrid-switch": (Switch, {}, "trending with no history, content with under 5 events, ALS with more"),
    "als+new": (WithNewSlots, {},
                "ALS with places for the closest new products (2 unless --set slots=N; from place 4; cold start)"),
}
