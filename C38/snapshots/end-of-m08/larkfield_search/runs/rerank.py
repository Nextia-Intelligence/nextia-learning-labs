"""Module 6 runs: a cross-encoder on the top candidates, and learning to rank."""

from .. import ltr, rerank, settings
from ..rules import with_codes
from . import register
from .dense import hybrid_rrf

RERANK = 50  # how many of the hybrid-rrf candidates the cross-encoder re-orders


@register("rerank-ce", "the top 50 of hybrid-rrf re-ordered by the cross-encoder (recorded scores; granite "
          "reranker english r2)", "M06")
def rerank_ce(query, query_id=None, k=100):
    n = int(settings.get("rerank", RERANK))
    cand = hybrid_rrf(query, query_id, max(k, 100))
    head = [p for p, _ in cand[:n]]
    s = rerank.scores(query, query_id, head)
    head = sorted(zip(head, s), key=lambda x: (-x[1], x[0]))
    return with_codes(query, head + cand[n:], k)


@register("ltr", "LambdaMART (LightGBM) on 19 features of the hybrid-rrf top 100, trained on the judgments of the "
          "training queries", "M06")
def ltr_judgments(query, query_id=None, k=100):
    return ltr.rank(query, query_id, "judgments", k)


@register("ltr-clicks", "the same model trained on clicks as labels (clicked when shown = 1)", "M06")
def ltr_clicks(query, query_id=None, k=100):
    return ltr.rank(query, query_id, "clicks", k)


@register("ltr-clicks-ipw", "trained on clicks divided by the chance of being looked at (position bias removed "
          "with the click model's ETA)", "M06")
def ltr_clicks_ipw(query, query_id=None, k=100):
    return ltr.rank(query, query_id, "clicks-ipw", k)
