"""Results by segment, because one average hides the customers and products a method fails.

Customer segments, by orders before the period: new (none), occasional (1 or 2), loyal (3 or more).
Product segment: new products (added in the last 60 days before the period).
"""


from . import metrics

SEGMENTS = ("new", "occasional", "loyal")


def by_segment(per, period):
    out = {}
    for seg in SEGMENTS:
        mask = period.segment == seg
        if not mask.any():
            continue
        out[seg] = {"customers": int(mask.sum()), "recall": float(per["recall"][mask].mean()),
                    "ndcg": float(per["ndcg"][mask].mean()),
                    "recall_ci": metrics.bootstrap(per["recall"][mask])[1:]}
    return out


def new_product_recall(recs, period, k=10):
    """Of the orders of new products in the period, the share that was in the customer's list."""
    new = period.new_products
    found = total = 0
    for row, truth in zip(recs[:, :k], period.truth):
        t = [p for p in truth if new[p]]
        total += len(t)
        found += len(set(t) & set(row.tolist()))
    return {"orders": int(total), "recall": float(found / total) if total else 0.0}
