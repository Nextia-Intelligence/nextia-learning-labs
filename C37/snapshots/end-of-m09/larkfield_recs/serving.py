"""Suggestions ready to serve: computed in a batch (each night), looked up in milliseconds, with a fallback.

`recs batch` trains a method on the whole log and writes outputs/batch/: the top 50 products of every known
customer, the trending list (the fallback) and the neighbours of every product (for the product page; content
neighbours for products with no history). The service only reads these files, so it starts fast and keeps working
with the fallback when the model's file is missing or broken.
"""

import json

import numpy as np

from . import data, registry
from . import rules as rules_mod
from .methods.content import Content
from .methods.neighbours import ItemItem
from .methods.popular import popular_list
from .paths import outputs_dir


def batch_dir():
    d = outputs_dir() / "batch"
    d.mkdir(parents=True, exist_ok=True)
    return d


def now_period(shop):
    last = int(shop.events.day.max())
    return data.Period(shop, "now", start_day=last + 1, end_day=last + 1)


def build(method="two-stage", shop=None, n=50):
    shop = shop or data.load()
    p = now_period(shop)
    known = np.unique(p.train.c.to_numpy())
    m = registry.make(method, p).fit()
    lists = np.vstack([m.recommend(known[i:i + 2000], n) for i in range(0, len(known), 2000)]) if len(known) else \
        np.empty((0, n), int)
    cf = ItemItem(p, kind="cosine").fit()
    ct = Content(p).fit()
    neigh = np.full((shop.n_products, 20), -1)
    for i in range(shop.n_products):
        idx, _ = cf.neighbours(i, 20)
        if len(idx) < 5:
            idx, _ = ct.similar(i, 20)
        neigh[i, : len(idx)] = idx
    d = batch_dir()
    np.savez(d / "lists.npz", customers=shop.customer_ids[known].astype(str), lists=lists, neighbours=neigh)
    fb = popular_list(p, days=28, n=200)
    (d / "fallback.json").write_text(json.dumps([shop.product_ids[i] for i in fb]) + "\n")
    meta = {"method": method, "trained_on_events_before": str(p.cutoff), "customers": len(known),
            "deleted_customers": sorted(data.deleted_customers())}
    (d / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


class Server:
    """What the service needs in memory: the batch lists (if any), the fallback and the rules."""

    def __init__(self, shop=None):
        self.shop = shop or data.load()
        self.rules = rules_mod.load()
        self.period = now_period(self.shop)
        self.block = rules_mod.blocked(self.period, self.rules)
        self.products = self.shop.products
        self.customers = self.shop.customers.set_index("customer_id")
        self.deleted = data.deleted_customers()
        d = batch_dir()
        self.meta, self.lists, self.neigh = None, {}, None
        try:
            z = np.load(d / "lists.npz", allow_pickle=False)
            self.lists = dict(zip(z["customers"].tolist(), z["lists"]))
            self.neigh = z["neighbours"]
            self.meta = json.loads((d / "meta.json").read_text())
        except (OSError, ValueError, KeyError):
            self.meta = None          # no model: every answer comes from the fallback
        try:
            self.fallback = [self.shop.product_index[x] for x in json.loads((d / "fallback.json").read_text())]
        except (OSError, ValueError):
            self.fallback = list(popular_list(self.period, days=28, n=200))

    def _clean(self, items, k, extra_block=None):
        out = []
        for p in items:
            if p < 0 or self.block[p] or (extra_block is not None and extra_block[p]) or p in out:
                continue
            out.append(int(p))
            if len(out) == k:
                break
        return out

    def recommend(self, customer_id, k=10, surface="home"):
        reason = None
        if customer_id in self.deleted:
            reason = "deleted"
        elif customer_id in self.customers.index and bool(self.customers.loc[customer_id, "opted_out"]):
            reason = "opted out of personal suggestions"
        items = self.lists.get(customer_id) if reason is None else None
        extra = None
        if surface == "email" and customer_id in self.customers.index and bool(self.customers.loc[customer_id, "shared_email"]):
            extra = self.products.sensitive.to_numpy(dtype=bool)   # never in a shared family inbox
        if items is None:
            return self._clean(self.fallback, k, extra), "fallback", reason or (
                "no model loaded" if self.meta is None else "no history for this customer")
        got = self._clean(items, k, extra)
        if len(got) < k:
            got += [p for p in self._clean(self.fallback, 2 * k, extra) if p not in got][: k - len(got)]
        return got, "model", None

    def similar(self, product_id, k=10):
        i = self.shop.product_index[product_id]
        if self.neigh is None:
            return self._clean(self.fallback, k), "fallback"
        return self._clean(self.neigh[i], k), "neighbours"

    def describe(self, items):
        pr = self.products
        return [{"product_id": self.shop.product_ids[i], "title": pr.title[i], "price": float(pr.price[i])} for i in items]
