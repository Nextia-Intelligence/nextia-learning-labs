"""Neighbour methods: "people also bought" (co-occurrence, lift, cosine) and user-user collaborative filtering.

Item-item: two products are neighbours when the same customers touched both. A customer gets the neighbours of
the products in their history, weighted by how strong and how recent each interaction was.
"""

import numpy as np
import scipy.sparse as sp

from . import Method, fill, top_k
from .popular import popular_list

HALF_LIFE_DAYS = 60


def history_matrix(period, half_life=HALF_LIFE_DAYS):
    """Customers × products: event weights, halved every `half_life` days before the period."""
    tr = period.train
    w = tr.event.map({"view": 1.0, "basket": 3.0, "order": 5.0}).astype(float).to_numpy()
    if half_life:
        w = w * 0.5 ** ((period.start_day - tr.day.to_numpy()) / half_life)
    m = sp.csr_matrix((w, (tr.c.to_numpy(), tr.p.to_numpy())), shape=(period.shop.n_customers, period.shop.n_products))
    m.sum_duplicates()
    return m


def item_similarity(period, kind="cosine", neighbours=50):
    """Products × products similarity from the customers who touched both (any event, counted once).

    cooc: the number of shared customers; lift: shared / expected if independent; cosine: shared / sqrt(n_i n_j).
    Only the `neighbours` strongest per product are kept."""
    b = period.matrix(binary=True).tocsc().astype(np.float32)
    co = (b.T @ b).tocsr().astype(np.float32)
    co.setdiag(0)
    co.eliminate_zeros()
    n_i = np.asarray(b.sum(axis=0)).ravel()
    co = co.tocoo()
    if kind == "cosine":
        val = co.data / np.sqrt(n_i[co.row] * n_i[co.col])
    elif kind == "lift":
        users = max(period.train.c.nunique(), 1)
        val = co.data * users / (n_i[co.row] * n_i[co.col])
        val = val * (co.data >= 2)          # one shared customer is not evidence
    else:
        val = co.data.astype(float)
    sim = sp.csr_matrix((val, (co.row, co.col)), shape=co.shape)
    sim.eliminate_zeros()
    return keep_top(sim, neighbours)


def keep_top(m, n):
    m = m.tocsr()
    rows, cols, vals = [], [], []
    for i in range(m.shape[0]):
        s, e = m.indptr[i], m.indptr[i + 1]
        if e == s:
            continue
        d, c = m.data[s:e], m.indices[s:e]
        if e - s > n:
            pick = np.argpartition(-d, n - 1)[:n]
            d, c = d[pick], c[pick]
        rows += [i] * len(c)
        cols += c.tolist()
        vals += d.tolist()
    return sp.csr_matrix((vals, (rows, cols)), shape=m.shape)


class ItemItem(Method):
    """Neighbours of the customer's products: cooc, lift or cosine similarity."""

    def fit(self):
        self.sim = item_similarity(self.period, self.settings.get("kind", "cosine"), self.settings.get("neighbours", 50))
        self.hist = history_matrix(self.period, self.settings.get("half_life", HALF_LIFE_DAYS))
        self.fallback = popular_list(self.period, days=28)
        return self

    def scores(self, users):
        return np.asarray((self.hist[users] @ self.sim).todense())

    def recommend(self, users, k=10):
        out = []
        for start in range(0, len(users), 2000):
            u = users[start:start + 2000]
            s = self.scores(u)
            s[s <= 0] = -np.inf
            out.append(top_k(s, k, self.period.available))
        return fill(np.vstack(out) if out else np.empty((0, k), int), self.fallback)

    def neighbours(self, product, n=10):
        row = self.sim[product]
        order = np.argsort(-row.data)[:n]
        return row.indices[order], row.data[order]


class UserUser(Method):
    """Products of the most similar customers (cosine over who touched what)."""

    def fit(self):
        self.hist = history_matrix(self.period, self.settings.get("half_life", HALF_LIFE_DAYS))
        b = self.period.matrix(binary=True)
        norms = np.sqrt(np.asarray(b.multiply(b).sum(axis=1)).ravel())
        norms[norms == 0] = 1
        self.unit = sp.diags(1 / norms) @ b
        self.fallback = popular_list(self.period, days=28)
        return self

    def recommend(self, users, k=10):
        n = self.settings.get("neighbours", 50)
        out = np.full((len(users), k), -1)
        for start in range(0, len(users), 500):
            u = users[start:start + 500]
            sims = (self.unit[u] @ self.unit.T).toarray()
            sims[np.arange(len(u)), u] = 0
            top = np.argpartition(-sims, n, axis=1)[:, :n]
            for i in range(len(u)):
                w = sims[i, top[i]]
                if w.max() <= 0:
                    continue
                s = np.asarray((sp.csr_matrix(w) @ self.hist[top[i]]).todense()).ravel()
                s[s <= 0] = -np.inf
                out[start + i] = top_k(s[None, :], k, self.period.available)[0]
        return fill(out, self.fallback)


METHODS = {
    "cooc": (ItemItem, {"kind": "cooc"}, "people also bought: products bought by the same customers (counts)"),
    "lift": (ItemItem, {"kind": "lift"}, "people also bought, by lift: shared customers against chance"),
    "item-cf": (ItemItem, {"kind": "cosine"}, "item-item collaborative filtering (cosine, 50 neighbours, recency)"),
    "user-user": (UserUser, {}, "user-user collaborative filtering (cosine, 50 similar customers)"),
}
