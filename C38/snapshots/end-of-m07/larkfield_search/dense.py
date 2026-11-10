"""Dense retrieval (Module 5): embeddings of queries and products, and a flat index (one matrix product).

The product embeddings are computed once by the course team and shipped in data/embeddings/ (float16, one row
per product in catalogue order), so no lesson waits for encoding. A query in the course's query set has its
embedding in the same folder; any other query is encoded on your computer with the same model (downloaded the
first time, about 200 MB).

Model: IBM granite-embedding-97m-multilingual-r2 (Apache-2.0), 384 numbers per text, cosine similarity.
"""

import json
import os
from functools import lru_cache

import numpy as np
import pandas as pd

from . import data
from .paths import data_dir


@lru_cache(maxsize=1)
def meta():
    return json.loads((data_dir() / "embeddings" / "model.json").read_text())


@lru_cache(maxsize=1)
def products():
    m = np.load(data_dir() / "embeddings" / "products.npy").astype(np.float32)
    if len(m) != len(data.catalogue()):
        raise SystemExit("data/embeddings/products.npy does not match the catalogue: download the data again.")
    return m


@lru_cache(maxsize=1)
def _known():
    q = data.queries()
    vecs = np.load(data_dir() / "embeddings" / "queries.npy").astype(np.float32)
    return {(qid, text): vecs[i] for i, (qid, text) in enumerate(zip(q["query_id"], q["query"]))}


@lru_cache(maxsize=1)
def model():
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(int(os.environ.get("LARKFIELD_THREADS", "4")))
    m = SentenceTransformer(meta()["model"], revision=meta()["revision"], device="cpu",
                            model_kwargs={"dtype": torch.float32})
    m.max_seq_length = meta()["max_tokens"]
    return m


def encode(text):
    """The embedding of a text, computed now (the model is loaded the first time)."""
    return model().encode([text], normalize_embeddings=True, convert_to_numpy=True)[0].astype(np.float32)


def query_vector(text, query_id=None):
    if os.environ.get("LARKFIELD_LIVE"):  # measure the real time: never use a shipped query embedding
        return encode(text)
    v = _known().get((query_id, text))
    return v if v is not None else encode(text)


def scores(text, query_id=None):
    """Cosine similarity of the query with every product (catalogue order)."""
    return products() @ query_vector(text, query_id)


def top(score, k=100):
    ids = data.catalogue()["product_id"].to_numpy()
    k = min(k, len(score))
    idx = np.argpartition(-score, k - 1)[:k]
    idx = idx[np.lexsort((ids[idx], -score[idx]))]
    return [(ids[i], float(score[i])) for i in idx]


def as_frame(results):
    return pd.DataFrame(results, columns=["product_id", "score"])
