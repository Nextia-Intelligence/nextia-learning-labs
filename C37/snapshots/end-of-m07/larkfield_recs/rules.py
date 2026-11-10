"""Business rules: remove products the shop must not suggest, then keep the list varied.

The rules file is rules.toml (in the folder where you run `recs`, or set LARKFIELD_RULES). Each rule removes
products from a long list; the list is then cut to k places, and empty places are filled with trending products
that pass the same rules.
"""

import os
import tomllib
from pathlib import Path

import numpy as np

from .methods.popular import popular_list

DEFAULTS = {"remove_out_of_stock": True, "remove_age_restricted": True, "remove_already_bought": True,
            "remove_sensitive": True, "min_margin": 0.0, "max_per_subcategory": 3}
STOCK_DAY = "2026-06-15"


def load(path=None):
    path = Path(path or os.environ.get("LARKFIELD_RULES", "rules.toml"))
    if not path.exists():
        path = Path(__file__).resolve().parent.parent / "rules.toml"
    rules = dict(DEFAULTS)
    if path.exists():
        rules.update(tomllib.loads(path.read_text())["rules"])
    return rules


def blocked(period, rules):
    """Products that no list may contain (the same for every customer)."""
    pr = period.shop.products
    out = ~period.available.copy()
    if rules.get("remove_out_of_stock") and period.start_day >= period.shop.day(STOCK_DAY):
        out |= ~pr.in_stock.to_numpy(dtype=bool)
    if rules.get("remove_age_restricted"):
        out |= pr.age_restricted.to_numpy(dtype=bool)
    if rules.get("remove_sensitive"):
        out |= pr.sensitive.to_numpy(dtype=bool)
    if rules.get("min_margin"):
        out |= pr.margin.to_numpy() < rules["min_margin"]
    return out


def apply(recs, period, rules, k=10, users=None):
    """Filter each long list with the rules, cap products per subcategory, cut to k, fill from trending."""
    shop = period.shop
    block = blocked(period, rules)
    bought = {}
    if rules.get("remove_already_bought"):
        repeat = shop.products.repeat_days.to_numpy() > 0
        o = period.train[period.train.event == "order"]
        o = o[~repeat[o.p.to_numpy()]]
        bought = o.groupby("c").p.agg(set).to_dict()
    sub = shop.products.subcategory.to_numpy()
    cap = rules.get("max_per_subcategory") or 10 ** 6
    trend = [p for p in popular_list(period, days=28, n=500) if not block[p]]
    out = np.full((len(recs), k), -1)
    users = period.users if users is None else users
    for i, (u, row) in enumerate(zip(users, recs)):
        have = bought.get(u, set())
        seen, per_sub = [], {}
        for p in list(row) + trend:
            if p < 0 or block[p] or p in have or p in seen:
                continue
            if per_sub.get(sub[p], 0) >= cap:
                continue
            per_sub[sub[p]] = per_sub.get(sub[p], 0) + 1
            seen.append(p)
            if len(seen) == k:
                break
        out[i, : len(seen)] = seen
    return out
