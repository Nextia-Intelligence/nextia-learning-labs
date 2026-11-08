"""The lexical indexes: SQLite FTS5 (Larkfield's search today) and BM25 per field (bm25s).

`search index` builds both into outputs/index/. A BM25 index for another field or analyzer is built the first
time a run needs it (a few seconds) and kept.

BM25 here is the Lucene form that bm25s uses: for each query word t in a product,
    idf(t) * tf / (tf + k1 * (1 - b + b * length / average length)),  idf(t) = ln(1 + (N - df + 0.5) / (df + 0.5))
(the classic formula multiplies by k1 + 1 as well; that changes every score by the same factor, never the order).
"""

import json
import shutil
import sqlite3
import time
from functools import lru_cache

import bm25s
import numpy as np

from . import data, text
from .paths import index_dir

K1, B = 1.2, 0.75
FIELDS = {
    "all": lambda r: f"{r.title} {r.description}",
    "title": lambda r: r.title,
    "description": lambda r: r.description,
    "category": lambda r: f"{r.product_class} {r.category}",
    "attributes": lambda r: f"{r.attributes} {r.colour} {r.style} {r.material}",
    "title_fr": lambda r: r.title_fr,
}


def fts_path():
    return index_dir() / "fts.sqlite"


def build_fts():
    """Larkfield's search today: SQLite FTS5 over the title and the description."""
    path = fts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    cat = data.catalogue()
    con = sqlite3.connect(path)
    con.execute("CREATE VIRTUAL TABLE products USING fts5(product_id UNINDEXED, title, description, "
                "tokenize = 'unicode61 remove_diacritics 2')")
    con.executemany("INSERT INTO products VALUES (?, ?, ?)",
                    zip(cat["product_id"], cat["title"], cat["description"]))
    con.commit()
    con.close()


@lru_cache(maxsize=1)
def fts():
    if not fts_path().exists():
        build_fts()
    return sqlite3.connect(fts_path(), check_same_thread=False)


def fts_search(query, k=100, mode="and"):
    """[(product_id, score)] from FTS5. mode "and": every word must be in the product (Larkfield today); "or": any."""
    words = text.tokens(query)
    if not words:
        return []
    joiner = " " if mode == "and" else " OR "
    match = joiner.join('"' + w.replace('"', '""') + '"' for w in words)
    rows = fts().execute("SELECT product_id, bm25(products) FROM products WHERE products MATCH ? "
                         "ORDER BY bm25(products) LIMIT ?", (match, k)).fetchall()
    return [(pid, -score) for pid, score in rows]  # FTS5's bm25() is lower-is-better


def _dir(field, analyzer):
    return index_dir() / f"bm25-{analyzer}-{field}"


def build_bm25(field, analyzer="plain"):
    cat = data.catalogue()
    tok = text.ANALYZERS[analyzer]
    corpus = [tok(FIELDS[field](r)) for r in cat.itertuples()]
    r = bm25s.BM25(k1=K1, b=B, method="lucene")
    r.index(corpus, show_progress=False)
    d = _dir(field, analyzer)
    if d.exists():
        shutil.rmtree(d)
    r.save(str(d))
    lengths = np.array([len(c) for c in corpus], dtype=np.int32)
    np.save(d / "lengths.npy", lengths)
    return r


_LOADED = {}


def bm25(field, analyzer="plain"):
    """The BM25 index of a field (built the first time, then loaded from outputs/index/)."""
    d = _dir(field, analyzer)
    key = (field, analyzer)
    if key in _LOADED and (d / "lengths.npy").exists():
        return _LOADED[key][0]
    r = build_bm25(field, analyzer) if not (d / "lengths.npy").exists() else bm25s.BM25.load(str(d))
    _LOADED[key] = (r, np.load(d / "lengths.npy"))
    return r


def lengths(field, analyzer="plain"):
    bm25(field, analyzer)
    return _LOADED[(field, analyzer)][1]


def scores(query, field="all", analyzer="plain"):
    """BM25 score of every product (catalogue order) for a query text."""
    r = bm25(field, analyzer)
    words = [w for w in text.ANALYZERS[analyzer](query) if w in r.vocab_dict]
    if not words:
        return np.zeros(len(data.catalogue()), dtype=np.float32)
    return r.get_scores(words)


def top(score, k=100):
    """[(product_id, score)] of the k best products with a score above 0, best first."""
    ids = data.catalogue()["product_id"].to_numpy()
    nz = np.flatnonzero(score > 0)
    if len(nz) == 0:
        return []
    if len(nz) > k:
        nz = nz[np.argpartition(-score[nz], k - 1)[:k]]
    nz = nz[np.lexsort((ids[nz], -score[nz]))]
    return [(ids[i], float(score[i])) for i in nz]


def build_all():
    """`search index`: FTS5 and the BM25 index of the title and description. Returns a short report."""
    t0 = time.time()
    build_fts()
    build_bm25("all")
    meta = {"products": len(data.catalogue()), "k1": K1, "b": B, "seconds": round(time.time() - t0, 1)}
    (index_dir() / "meta.json").write_text(json.dumps(meta, indent=1))
    fts.cache_clear()
    _LOADED.clear()
    return meta


def size_mb():
    return sum(p.stat().st_size for p in index_dir().rglob("*") if p.is_file()) / 1e6
