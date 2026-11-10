"""Module 4 runs: normalise and stem, fix spelling, add synonyms, rewrite with a language model, detect filters.

Every run from Module 4 on keeps the code rule of Module 3 (rules.with_codes).
"""

import json
from functools import lru_cache

import numpy as np

from .. import data, index, settings, spell, synonyms
from ..detect import detect
from ..paths import data_dir
from ..rules import with_codes
from . import register
from .fields import WEIGHTS

FRENCH_TITLE_WEIGHT = 1.0  # the French title (stemmed in French), for French queries


def norm_scores(query):
    """BM25 per field after normalising and stemming (English fields) plus the French title (French stems)."""
    w = settings.weights(WEIGHTS)
    total = sum(wt * index.scores(query, f, "norm") for f, wt in w.items() if wt)
    fr = settings.get("title_fr", FRENCH_TITLE_WEIGHT)
    if fr:
        total = total + fr * index.scores(query, "title_fr", "norm_fr")
    return total


def with_synonyms(query, base=norm_scores):
    s = base(query)
    extra = synonyms.expansion(query)
    if extra:
        s = s + settings.get("synonym_weight", synonyms.EXPANSION_WEIGHT) * base(extra)
    return s


@register("bm25-norm", "bm25-fields after normalising and stemming, plus French titles for French words", "M04")
def bm25_norm(query, query_id=None, k=100):
    return with_codes(query, index.top(norm_scores(query), k), k)


@register("bm25-norm+spell", "bm25-norm after correcting words that are not in the dictionary", "M04")
def bm25_spell(query, query_id=None, k=100):
    return with_codes(query, index.top(norm_scores(spell.correct(query)[0]), k), k)


@register("bm25-norm+spell+syn", "bm25-norm+spell, plus the synonym rules of data/synonyms.csv", "M04")
def bm25_spell_syn(query, query_id=None, k=100):
    return with_codes(query, index.top(with_synonyms(spell.correct(query)[0]), k), k)


@lru_cache(maxsize=1)
def rewrites():
    path = data_dir() / "recorded" / "llm_rewrites.jsonl"
    return {r["query_id"]: r["rewrite"] for r in map(json.loads, path.read_text().splitlines())}


@register("llm-rewrite", "bm25-norm on the query rewritten by a language model (recorded answers; the query "
          "itself when there is no recorded answer)", "M04")
def llm_rewrite(query, query_id=None, k=100):
    return with_codes(query, index.top(norm_scores(rewrites().get(query_id, query)), k), k)


@register("bm25-norm+spell+syn+detect", "bm25-norm+spell+syn, plus a price filter and a boost for the product "
          "class that the classifier guesses", "M04")
def bm25_detect(query, query_id=None, k=100):
    d = detect(query)
    s = with_synonyms(spell.correct(d["clean"])[0])
    cat = data.catalogue()
    if d["classes"]:
        s = s * np.where(cat["product_class"].isin(d["classes"]), settings.get("class_boost", 1.3), 1.0)
    if d["price_max"] is not None:
        s = np.where(cat["price"] <= d["price_max"], s, 0)
    return with_codes(query, index.top(s, k), k)
