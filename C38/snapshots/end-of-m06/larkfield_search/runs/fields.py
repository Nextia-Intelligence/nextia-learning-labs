"""Module 3 runs: BM25 per field with weights, and the exact-match rule for product codes."""

from .. import index, settings
from ..rules import with_codes
from . import register

# Field weights tuned on the validation queries (a grid of 96 settings; Module 3, lesson 2). The title needs no
# extra weight here (its words are in the description too); the attributes field hurts, so it gets 0.
WEIGHTS = {"title": 1.0, "description": 1.0, "category": 0.5, "attributes": 0.0}


def weighted(query, weights=None, analyzer="plain"):
    """The weighted sum of the BM25 scores of each field."""
    weights = settings.weights(weights or WEIGHTS)
    total = None
    for field, w in weights.items():
        if w:
            s = w * index.scores(query, field, analyzer)
            total = s if total is None else total + s
    return total


@register("bm25-title", "BM25 on the title only", "M03")
def bm25_title(query, query_id=None, k=100):
    return index.top(index.scores(query, "title"), k)


@register("bm25-fields", "BM25 per field with weights tuned on validation: title 1, description 1, category 0.5, attributes 0", "M03")
def bm25_fields(query, query_id=None, k=100):
    return index.top(weighted(query), k)


@register("bm25-fields+codes", "bm25-fields, and a product code in the query puts that product first", "M03")
def bm25_fields_codes(query, query_id=None, k=100):
    return with_codes(query, index.top(weighted(query), k), k)

