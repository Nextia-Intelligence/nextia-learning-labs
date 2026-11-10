"""Beyond accuracy: is the list useful, or correct but boring?

- novelty: how surprising the suggestions are, in bits: -log2(share of training customers who touched the
  product). A product that everybody saw has a low novelty.
- diversity: the share of pairs in a list that come from different subcategories (0 = all the same kind).
- new_share: the share of all suggestions that are new products (added in the last 60 days).
- top_share: the share of all suggestions taken by the 1% most popular products (popularity bias).
"""

import numpy as np


def measures(recs, period, k=10):
    r = recs[:, :k]
    shown = r[r >= 0]
    users = max(period.train.c.nunique(), 1)
    info = -np.log2((period.item_customers + 1) / (users + 1))
    sub = period.shop.products.subcategory.to_numpy()
    div = []
    for row in r:
        row = row[row >= 0]
        if len(row) < 2:
            continue
        s = sub[row]
        same = (s[:, None] == s[None, :]).sum() - len(row)
        div.append(1 - same / (len(row) * (len(row) - 1)))
    top = np.argsort(-period.item_customers)[: max(1, int(0.01 * period.available.sum()))]
    return {
        "novelty": float(info[shown].mean()) if len(shown) else 0.0,
        "diversity": float(np.mean(div)) if div else 0.0,
        "new_share": float(period.new_products[shown].mean()) if len(shown) else 0.0,
        "top_share": float(np.isin(shown, top).mean()) if len(shown) else 0.0,
    }
