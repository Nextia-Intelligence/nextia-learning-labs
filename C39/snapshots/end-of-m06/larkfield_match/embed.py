"""Embeddings for names, addresses and products (Module 6, lesson 3).

A small multilingual model turns each record's text into 384 numbers; similar texts get similar numbers. The
course data has every record's embedding already (data/embeddings/), so no lesson waits for the model. They are
stored as 8-bit integers with one scale per row (a quarter of the size of float32); `encode` makes new ones.
"""

import json
import os

import numpy as np
import pandas as pd

from . import prepared
from .paths import data_dir

MODEL = "ibm-granite/granite-embedding-97m-multilingual-r2"
REVISION = "835ad14087e140460703cf0fae09f97d469d65c2"


def record_text(df):
    """What the model reads for a customer: the name and the address (or the postcode when there is no address)."""
    addr = (df.number + " " + df.street + " " + df.town).str.strip()
    addr = addr.where(addr != "", df.postcode)
    return (df.full + ", " + addr).str.strip(", ")


def product_text(df):
    """What the model reads for a product: the title as the feed wrote it (with sizes and packs)."""
    return df.title


def encode(texts, batch_size=64):
    """Embeddings from the model (downloads it the first time, about 200 MB). float32, one row per text."""
    from . import torch_first
    torch_first()
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(int(os.environ.get("LARKFIELD_THREADS", "4")))
    # the weights are stored in bfloat16, which is slow on most CPUs: load them as float32
    model = SentenceTransformer(MODEL, revision=REVISION, device="cpu", model_kwargs={"dtype": torch.float32})
    e = model.encode(list(texts), batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False,
                     convert_to_numpy=True)
    return e.astype("float32")


def quantize(e):
    """float32 rows -> int8 rows and one float32 scale per row."""
    scale = np.abs(e).max(axis=1, keepdims=True) / 127.0
    scale[scale == 0] = 1.0
    return np.round(e / scale).astype("int8"), scale.astype("float32")


def load(dataset):
    """The shipped embeddings of a dataset as normalised float32 rows, and the record IDs in the same order."""
    d = data_dir() / "embeddings"
    q = np.load(d / f"{dataset}_int8.npy").astype("float32")
    e = q * np.load(d / f"{dataset}_scale.npy")
    e /= np.linalg.norm(e, axis=1, keepdims=True)
    ids = pd.read_csv(d / f"{dataset}_ids.csv", dtype=str).record_id.tolist()
    return e, ids


def meta():
    return json.loads((data_dir() / "embeddings" / "model.json").read_text())


def cosine_pairs(pairs, dataset):
    """Cosine similarity of each pair's two embeddings."""
    e, ids = load(dataset)
    row = {r: i for i, r in enumerate(ids)}
    a = e[[row[r] for r in pairs.record_id_l]]
    b = e[[row[r] for r in pairs.record_id_r]]
    return (a * b).sum(axis=1)


def nearest_pairs(dataset="customers", k=10, chunk=1000):
    """Each record with its k most similar records (by cosine): candidate pairs from embeddings."""
    e, ids = load(dataset)
    ids = np.array(ids)
    rows_l, rows_r, sims = [], [], []
    for s in range(0, len(e), chunk):
        sim = e[s:s + chunk] @ e.T
        for i in range(sim.shape[0]):
            sim[i, s + i] = -1.0
        top = np.argpartition(-sim, k, axis=1)[:, :k]
        rows_l.append(np.repeat(ids[s:s + chunk], k))
        rows_r.append(ids[top.ravel()])
        sims.append(np.take_along_axis(sim, top, axis=1).ravel())
    df = pd.DataFrame({"a": np.concatenate(rows_l), "b": np.concatenate(rows_r), "cosine": np.concatenate(sims)})
    df["record_id_l"] = df[["a", "b"]].min(axis=1)
    df["record_id_r"] = df[["a", "b"]].max(axis=1)
    return df.drop_duplicates(["record_id_l", "record_id_r"])[["record_id_l", "record_id_r", "cosine"]]


def build(out_dir):
    """Encode every customer and product of the course data and write data/embeddings/ (authors only)."""
    import time
    from pathlib import Path
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    info = {"model": MODEL, "revision": REVISION, "dimensions": 384, "stored_as": "int8 with one float32 scale per row"}
    for ds, df, fn in (("customers", prepared.customers(), record_text), ("products", prepared.products(), product_text)):
        t0 = time.perf_counter()
        e = encode(fn(df).tolist())
        secs = time.perf_counter() - t0
        q, scale = quantize(e)
        np.save(out_dir / f"{ds}_int8.npy", q)
        np.save(out_dir / f"{ds}_scale.npy", scale)
        df[["record_id"]].to_csv(out_dir / f"{ds}_ids.csv", index=False)
        back = q.astype("float32") * scale
        back /= np.linalg.norm(back, axis=1, keepdims=True)
        info[ds] = {"rows": len(df), "seconds": round(secs, 1), "per_second": round(len(df) / secs, 1),
                    "max_cosine_error_int8": float(np.abs((back * e).sum(axis=1) - 1).max())}
    (out_dir / "model.json").write_text(json.dumps(info, indent=1) + "\n")
    return info
