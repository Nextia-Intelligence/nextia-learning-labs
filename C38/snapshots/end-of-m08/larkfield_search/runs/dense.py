"""Module 5 runs: dense retrieval and two kinds of hybrid search."""

import numpy as np

from .. import dense, index, settings, spell
from ..rules import with_codes
from . import register
from .understand import with_synonyms

RRF_K = 60       # reciprocal rank fusion: 1 / (RRF_K + rank)
DEPTH = 100      # how many results of each list are fused
ALPHA = 0.8      # score blending: ALPHA * lexical + (1 - ALPHA) * dense (each scaled to 0..1); tuned on validation


def lexical_scores(query):
    """The best lexical search of Module 4 (normalised, spelling, synonyms) as one score per product."""
    return with_synonyms(spell.correct(query)[0])


@register("dense", "cosine similarity of multilingual embeddings (granite-embedding-97m-multilingual-r2)", "M05")
def dense_run(query, query_id=None, k=100):
    return with_codes(query, dense.top(dense.scores(query, query_id), k), k)


def rrf(lists, k_rrf=RRF_K):
    """Reciprocal rank fusion of ranked lists of product IDs: sum of 1 / (k_rrf + rank)."""
    total = {}
    for ranked in lists:
        for r, pid in enumerate(ranked, 1):
            total[pid] = total.get(pid, 0.0) + 1.0 / (k_rrf + r)
    return sorted(total.items(), key=lambda kv: (-kv[1], kv[0]))


@register("hybrid-rrf", "reciprocal rank fusion (k 60) of the top 100 of bm25-norm+spell+syn and of dense", "M05")
def hybrid_rrf(query, query_id=None, k=100):
    depth = int(settings.get("depth", DEPTH))
    lex = [p for p, _ in index.top(lexical_scores(query), depth)]
    den = [p for p, _ in dense.top(dense.scores(query, query_id), depth)]
    return with_codes(query, rrf([lex, den], settings.get("rrf_k", RRF_K))[:k], k)


def blend_scores(query, query_id=None, alpha=None):
    alpha = settings.get("alpha", ALPHA) if alpha is None else alpha
    lex = lexical_scores(query)
    den = dense.scores(query, query_id)
    lex = lex / lex.max() if lex.max() > 0 else lex
    depth = min(DEPTH, len(den))
    top = np.partition(den, -depth)[-depth:]
    lo, hi = float(top.min()), float(top.max())
    den = np.clip((den - lo) / (hi - lo), 0, 1) if hi > lo else den * 0
    return alpha * lex + (1 - alpha) * den


@register("hybrid-blend", "score blending: 0.8 x lexical (scaled by its best score) + 0.2 x dense (scaled 0..1 "
          "over its top 100)", "M05")
def hybrid_blend(query, query_id=None, k=100):
    return with_codes(query, dense.top(blend_scores(query, query_id), k), k)
