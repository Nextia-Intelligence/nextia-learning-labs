"""More baselines: recently trending products, and popular products of each customer's favourite categories."""

import numpy as np

from . import Method, top_k
from .popular import Popular, popularity


class PopularByCategory(Method):
    """The most ordered products of each customer's favourite categories (by their past events); popular for the rest."""

    def fit(self):
        shop, tr = self.shop, self.period.train
        self.pop = popularity(self.period, self.settings.get("days"))
        cats, self.cat_of = np.unique(shop.products.category.to_numpy(), return_inverse=True)
        w = tr.event.map({"view": 1.0, "basket": 3.0, "order": 5.0}).astype(float).to_numpy()
        self.user_cat = np.zeros((shop.n_customers, len(cats)))
        np.add.at(self.user_cat, (tr.c.to_numpy(), self.cat_of[tr.p.to_numpy()]), w)
        return self

    def recommend(self, users, k=10):
        out = np.full((len(users), k), -1)
        overall = top_k(self.pop[None, :], k, self.period.available)[0]
        ranked = {}
        for i, u in enumerate(users):
            uc = self.user_cat[u]
            if uc.sum() == 0:
                out[i] = overall
                continue
            # share the k places between categories in proportion to the customer's events
            share = uc / uc.sum()
            places = np.floor(share * k).astype(int)
            for j in np.argsort(-share)[: k - places.sum()]:
                places[j] += 1
            row = []
            for c in np.argsort(-places):
                if places[c] == 0:
                    break
                if c not in ranked:
                    s = np.where((self.cat_of == c) & self.period.available, self.pop, -np.inf)
                    ranked[c] = top_k(s[None, :], 50, None)[0]
                row += [p for p in ranked[c] if p >= 0][: places[c]]
            row = (row + [p for p in overall if p not in row])[:k]
            out[i] = row
        return out


METHODS = {
    "trending": (Popular, {"days": 28}, "the most ordered products of the last 28 days"),
    "popular-category": (PopularByCategory, {}, "the most ordered products of each customer's favourite categories"),
}
