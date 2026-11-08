"""Module 7 runs: zero-result fallbacks, business rules and an exploration slot for new products."""

from .. import business
from . import register
from .rerank import ltr_judgments

DEPTH = 100  # a rule re-orders the whole ltr top 100, also when only the top 10 is shown (search query)


def _ltr(query, query_id):
    return ltr_judgments(query, query_id, DEPTH)


@register("current+fallback", "Larkfield's search today, but never empty: all words, else any word, else by meaning",
          "M07")
def current_fallback(query, query_id=None, k=100):
    return business.fallback(query, query_id, k)[0]


@register("ltr+sale-first", "ltr, then every sale item first (Hana's request)", "M07")
def ltr_sale_first(query, query_id=None, k=100):
    return business.sale_first(_ltr(query, query_id))[:k]


@register("ltr+sale-boost", "ltr, sale items moved up by 20% of the score range", "M07")
def ltr_sale_boost(query, query_id=None, k=100):
    return business.sale_boost(_ltr(query, query_id))[:k]


@register("ltr+stock-last", "ltr, out-of-stock products after the products in stock", "M07")
def ltr_stock(query, query_id=None, k=100):
    return business.stock_last(_ltr(query, query_id))[:k]


@register("ltr+explore", "ltr, with the best new product (no clicks yet) at position 4", "M07")
def ltr_explore(query, query_id=None, k=100):
    return business.explore(_ltr(query, query_id))[:k]
