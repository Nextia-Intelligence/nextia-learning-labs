"""Re-rank with a cross-encoder (Module 6, lesson 2): read the query and the product together.

The course team scored the top 100 candidates of `hybrid-rrf` for every validation and test query once, and
ships the scores (data/recorded/rerank.csv.gz). Any other pair is scored on your computer with the same model,
downloaded the first time (about 600 MB): IBM granite-embedding-reranker-english-r2 (Apache-2.0).
"""

import os
from functools import lru_cache

import pandas as pd

from . import data
from .embedtext import product_text
from .paths import data_dir

MODEL = "ibm-granite/granite-embedding-reranker-english-r2"
REVISION = "d09d3d6971b689bf9c23839e45a470874d46e13a"
MAX_TOKENS = 256


@lru_cache(maxsize=1)
def recorded():
    df = pd.read_csv(data_dir() / "recorded" / "rerank.csv.gz")
    return dict(zip(zip(df["query_id"], df["product_id"]), df["score"]))


@lru_cache(maxsize=1)
def model():
    import torch
    from sentence_transformers import CrossEncoder
    torch.set_num_threads(int(os.environ.get("LARKFIELD_THREADS", "4")))
    return CrossEncoder(MODEL, revision=REVISION, device="cpu", max_length=MAX_TOKENS,
                        model_kwargs={"dtype": torch.float32})


def live(query, product_ids):
    cat = data.catalogue().set_index("product_id")
    pairs = [(query, product_text(cat.loc[p, "title"], cat.loc[p, "product_class"], cat.loc[p, "description"]))
             for p in product_ids]
    return [float(s) for s in model().predict(pairs, batch_size=32, show_progress_bar=False)]


def scores(query, query_id, product_ids, allow_live=True):
    """Cross-encoder scores of the products for the query: recorded when the course has them, else computed."""
    rec = {} if os.environ.get("LARKFIELD_LIVE") else recorded()  # LARKFIELD_LIVE: always run the model
    got = [rec.get((query_id, p)) for p in product_ids]
    missing = [p for p, s in zip(product_ids, got) if s is None]
    if missing:
        if not allow_live:
            raise KeyError(f"no recorded scores for {len(missing)} products of {query_id}")
        fresh = dict(zip(missing, live(query, missing)))
        got = [fresh[p] if s is None else s for p, s in zip(product_ids, got)]
    return got
