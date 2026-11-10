"""Next-item suggestions from the current visit (session): what will this visitor look at next?

- markov: the products most often viewed right after the current product in past visits.
- item-cf: the item-item neighbours of the current product (who touched both, at any time).
- trending: the same list for everyone (the most ordered products of the last 28 days).
Scored on the test period's visits: for each view after the first, did the list (from the view before) contain it?
"""

import numpy as np
import scipy.sparse as sp

from . import data
from .methods import top_k
from .methods.neighbours import item_similarity
from .methods.popular import popularity


def transitions(events, n):
    v = events[events.event == "view"].sort_values(["session", "ts"])
    same = v.session.to_numpy()[1:] == v.session.to_numpy()[:-1]
    a, b = v.p.to_numpy()[:-1][same], v.p.to_numpy()[1:][same]
    keep = a != b
    m = sp.csr_matrix((np.ones(keep.sum()), (a[keep], b[keep])), shape=(n, n))
    m.sum_duplicates()
    return m


def test_pairs(period):
    ev = period.shop.events
    v = ev[(ev.day >= period.start_day) & (ev.day <= period.end_day) & (ev.event == "view")].sort_values(["session", "ts"])
    same = v.session.to_numpy()[1:] == v.session.to_numpy()[:-1]
    a, b = v.p.to_numpy()[:-1][same], v.p.to_numpy()[1:][same]
    keep = a != b
    return a[keep], b[keep]


def evaluate(shop=None, k=10):
    shop = shop or data.load()
    p = data.Period(shop, "test")
    n = shop.n_products
    cur, nxt = test_pairs(p)
    trans = transitions(p.train, n)
    sim = item_similarity(p, "cosine", 50)
    trend = popularity(p, 28)
    out = {}
    for name in ("markov", "item-cf", "markov+trending", "trending"):
        hits, rr = [], []
        for start in range(0, len(cur), 5000):
            c = cur[start:start + 5000]
            if name == "trending":
                s = np.tile(trend, (len(c), 1))
            elif name == "markov":
                s = trans[c].toarray()
            elif name == "item-cf":
                s = sim[c].toarray()
            else:
                s = trans[c].toarray()
                s = s / np.maximum(s.max(axis=1, keepdims=True), 1) + 0.01 * trend / trend.max()
            s[s <= 0] = -np.inf
            s[np.arange(len(c)), c] = -np.inf
            rec = top_k(s, k, p.available)
            nx = nxt[start:start + 5000]
            pos = (rec == nx[:, None])
            hit = pos.any(axis=1)
            rank = np.where(hit, pos.argmax(axis=1) + 1, 0)
            hits.append(hit)
            rr.append(np.where(hit, 1.0 / np.maximum(rank, 1), 0.0))
        h, r = np.concatenate(hits), np.concatenate(rr)
        out[name] = {"hit": float(h.mean()), "mrr": float(r.mean())}
    out["pairs"] = len(cur)
    return out
