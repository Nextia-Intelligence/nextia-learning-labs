"""Zero results, business rules and the cold start (Module 7, lessons 3 and 4).

Each rule takes a ranked list [(product_id, score)] and returns a new one, so its cost in relevance can be
measured like any other run.
"""

from . import data, dense, index

NEW_FROM = "2025-10-13"  # products added in the last two weeks of the log have (almost) no clicks


def _col(name):
    cat = data.catalogue()
    return dict(zip(cat["product_id"], cat[name]))


def sale_first(results):
    """Hana's request: every sale item before every other item (the order inside each group stays)."""
    sale = _col("on_sale")
    return [r for r in results if sale[r[0]]] + [r for r in results if not sale[r[0]]]


def sale_boost(results, boost=0.2):
    """A softer rule: a sale item moves up by `boost` of the score range of the list."""
    if not results:
        return results
    sale = _col("on_sale")
    lo, hi = min(s for _, s in results), max(s for _, s in results)
    bonus = boost * (hi - lo)
    return sorted(((p, s + bonus * sale[p]) for p, s in results), key=lambda x: (-x[1], x[0]))


def stock_last(results):
    """Out-of-stock products after every product in stock."""
    stock = _col("in_stock")
    return [r for r in results if stock[r[0]]] + [r for r in results if not stock[r[0]]]


def fallback(query, query_id=None, k=100):
    """Never an empty page: every word must match; if nothing does, any word; if nothing does, by meaning."""
    res = index.fts_search(query, k, "and")
    if res:
        return res, "all words"
    res = index.fts_search(query, k, "or")
    if res:
        return res, "any word"
    return dense.top(dense.scores(query, query_id), k), "by meaning"


def explore(results, slot=4):
    """An exploration slot: the best new product (added in the last two weeks) among the candidates goes to
    position `slot`, so new products get seen and can earn clicks."""
    added = _col("added")
    new = [r for r in results if added[r[0]] >= NEW_FROM]
    if not new or new[0] in results[:slot]:
        return results
    rest = [r for r in results if r[0] != new[0][0]]
    return rest[: slot - 1] + [new[0]] + rest[slot - 1:]


def share(results, column, n=10):
    """The share of the top n that has column == True (for example on_sale or in_stock)."""
    flag = _col(column)
    top = results[:n]
    return sum(bool(flag[p]) for p, _ in top) / len(top) if top else float("nan")

