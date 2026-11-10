"""Read the shop log and make the evaluation periods.

The shop log is synthetic: made by the course's code with a model of customer behaviour. Every event is one row:
a customer viewed a product, added it to the basket, or ordered it.

A Period is one honest test: train on every event before its first day, then predict the products that each
customer ordered during the period. `validation` is for tuning; `test` is used once; `launch` replays the
first two weeks of the new summer range (cold start). `random` is the mistake we
measure in the lessons: orders held out at random from the whole log, so the training data contains the future.
"""

import hashlib
import json
import pickle
from dataclasses import dataclass, field
from functools import cached_property

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .paths import data_dir, outputs_dir

EVENT_WEIGHTS = {"view": 1.0, "basket": 3.0, "order": 5.0}
LOG_START = pd.Timestamp("2025-02-01")
NEW_PRODUCT_DAYS = 60  # a product added in the last 60 days before a period is "new"


def checksums():
    f = data_dir() / "SHA256SUMS"
    if not f.exists():
        return {}
    out = {}
    for line in f.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.strip()] = digest
    return out


def verify():
    """Names of data files that are missing or changed."""
    bad = []
    for name, digest in checksums().items():
        p = data_dir() / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(name)
    return bad


def deleted_customers():
    f = outputs_dir() / "deleted.txt"
    return set(f.read_text().split()) if f.exists() else set()


@dataclass
class Shop:
    products: pd.DataFrame
    customers: pd.DataFrame
    events: pd.DataFrame          # c, p, event, day, session, quantity, price, ts
    splits: dict
    customer_ids: np.ndarray
    product_ids: np.ndarray
    removed: int = 0              # events removed by deletion requests
    _cache: dict = field(default_factory=dict, repr=False)

    @property
    def n_customers(self):
        return len(self.customer_ids)

    @property
    def n_products(self):
        return len(self.product_ids)

    def day(self, date):
        return (pd.Timestamp(date) - LOG_START).days

    @cached_property
    def product_index(self):
        return {p: i for i, p in enumerate(self.product_ids)}

    @cached_property
    def customer_index(self):
        return {c: i for i, c in enumerate(self.customer_ids)}

    @cached_property
    def added_day(self):
        return ((pd.to_datetime(self.products.added) - LOG_START).dt.days).to_numpy()


def _read():
    d = data_dir()
    products = pd.read_csv(d / "products.csv", keep_default_na=False, na_values=[])
    customers = pd.read_csv(d / "customers.csv")
    ev = pd.read_csv(d / "events.csv.gz", dtype={"event": "category"})
    splits = json.loads((d / "splits.json").read_text())
    pid = products.product_id.to_numpy()
    cid = customers.customer_id.to_numpy()
    p_index = pd.Series(np.arange(len(pid)), index=pid)
    c_index = pd.Series(np.arange(len(cid)), index=cid)
    ts = pd.to_datetime(ev.timestamp, format="%Y-%m-%d %H:%M:%S")
    events = pd.DataFrame({
        "c": c_index.reindex(ev.customer_id).to_numpy(), "p": p_index.reindex(ev.product_id).to_numpy(),
        "event": ev.event, "day": (ts - LOG_START).dt.days.to_numpy(), "ts": ts,
        "session": ev.session_id.str[1:].astype(np.int64).to_numpy(), "quantity": ev.quantity, "price": ev.price})
    return products, customers, events, splits, cid, pid


def load():
    """The shop log (cached in outputs/cache/ after the first read), without the customers in outputs/deleted.txt."""
    d = data_dir()
    f = d / "events.csv.gz"
    key = hashlib.sha256(f"{f.resolve()}:{f.stat().st_size}:{f.stat().st_mtime_ns}".encode()).hexdigest()[:16]
    cache = outputs_dir() / "cache" / f"shop-{key}.pkl"
    if cache.exists():
        parts = pickle.loads(cache.read_bytes())
    else:
        parts = _read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        for old in cache.parent.glob("shop-*.pkl"):
            old.unlink()
        cache.write_bytes(pickle.dumps(parts, protocol=pickle.HIGHEST_PROTOCOL))
    products, customers, events, splits, cid, pid = parts
    gone = deleted_customers()
    removed = 0
    if gone:
        idx = np.flatnonzero(np.isin(cid, list(gone)))
        keep = ~events.c.isin(idx).to_numpy()
        removed = int((~keep).sum())
        events = events[keep].reset_index(drop=True)
    return Shop(products, customers, events, splits, cid, pid, removed)


def interaction_matrix(events, n_customers, n_products, weights=EVENT_WEIGHTS, binary=False):
    """Customers × products, the sum of the event weights (or 1 where there is any event)."""
    w = events.event.map(weights).astype(float).fillna(0).to_numpy()
    m = sp.csr_matrix((w, (events.c.to_numpy(), events.p.to_numpy())), shape=(n_customers, n_products))
    m.sum_duplicates()
    if binary:
        m.data[:] = 1.0
    return m.astype(np.float32)


class Period:
    """One evaluation period: the training events, the customers to score and the products they ordered."""

    def __init__(self, shop, name="test", quick=False, seed=37, quick_size=1000, start_day=None, end_day=None):
        self.shop, self.name = shop, name
        ev = shop.events
        if start_day is not None:          # any window, for example the weeks before a period (ranker training)
            self.start_day, self.end_day = start_day, end_day
            self.train = ev[ev.day < start_day]
            self._targets(ev[(ev.day >= start_day) & (ev.day <= end_day) & (ev.event == "order")])
        elif name == "random":
            self._random(shop, seed)
        else:
            first, last = shop.splits[name]
            self.start_day, self.end_day = shop.day(first), shop.day(last)
            self.train = ev[ev.day < self.start_day]
            target = ev[(ev.day >= self.start_day) & (ev.day <= self.end_day) & (ev.event == "order")]
            self._targets(target)
        if quick and len(self.users) > quick_size:
            pick = np.sort(np.random.default_rng(seed).choice(len(self.users), quick_size, replace=False))
            self.users = self.users[pick]
            self.truth = [self.truth[i] for i in pick]
        self.available = shop.added_day <= self.start_day          # on sale on the period's first day
        self.new_products = self.available & (shop.added_day > self.start_day - NEW_PRODUCT_DAYS)

    def _targets(self, target):
        g = target.groupby("c").p.unique()
        self.users = g.index.to_numpy()
        self.truth = [np.asarray(v) for v in g.to_numpy()]

    def _random(self, shop, seed):
        """Hold out orders at random from the whole public log (the leaky split)."""
        ev = shop.events
        last = shop.day(shop.splits["test"][1])
        first = shop.day(shop.splits["test"][0])
        test_users = ev[(ev.day >= first) & (ev.event == "order")].c.nunique()
        orders = ev[ev.event == "order"][["c", "p"]].drop_duplicates()
        rng = np.random.default_rng(seed)
        held = orders.iloc[rng.permutation(len(orders))[: int(len(orders) * 0.05)]]
        users = held.c.unique()
        users = np.sort(rng.choice(users, min(test_users, len(users)), replace=False))
        held = held[held.c.isin(users)]
        pair = ev.c.to_numpy().astype(np.int64) * shop.n_products + ev.p.to_numpy()
        held_pair = held.c.to_numpy().astype(np.int64) * shop.n_products + held.p.to_numpy()
        self.train = ev[~np.isin(pair, held_pair)]
        self.start_day, self.end_day = first, last   # products available as in the test period
        self._targets(held)

    @property
    def cutoff(self):
        return (LOG_START + pd.Timedelta(days=self.start_day)).date()

    def matrix(self, weights=EVENT_WEIGHTS, binary=False):
        key = (tuple(sorted(weights.items())), binary)
        if key not in self.__dict__.setdefault("_m", {}):
            self._m[key] = interaction_matrix(self.train, self.shop.n_customers, self.shop.n_products, weights, binary)
        return self._m[key]

    @cached_property
    def orders_before(self):
        """Number of orders (sessions with an order) of every customer before the period."""
        o = self.train[self.train.event == "order"].groupby("c").session.nunique()
        out = np.zeros(self.shop.n_customers, dtype=np.int64)
        out[o.index.to_numpy()] = o.to_numpy()
        return out

    @cached_property
    def segment(self):
        """new (no order before), occasional (1 or 2 orders), loyal (3 or more) for each scored customer."""
        n = self.orders_before[self.users]
        return np.where(n == 0, "new", np.where(n <= 2, "occasional", "loyal"))

    @cached_property
    def item_customers(self):
        """How many training customers interacted with each product (any event)."""
        pairs = self.train[["c", "p"]].drop_duplicates()
        return np.bincount(pairs.p.to_numpy(), minlength=self.shop.n_products)
