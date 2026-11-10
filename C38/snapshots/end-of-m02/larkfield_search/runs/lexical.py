"""Lexical runs of the setup lesson: Larkfield's search today and plain BM25."""

from .. import index
from . import register


@register("current", "Larkfield's search today: SQLite FTS5, every word must match, title and description",
          "M01")
def current(query, query_id=None, k=100):
    return index.fts_search(query, k, mode="and")


@register("bm25", "BM25 (k1 1.2, b 0.75) on the title and the description as one field; any word may match",
          "M01")
def bm25(query, query_id=None, k=100):
    return index.top(index.scores(query, "all"), k)
