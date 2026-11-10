"""Blocking: compare only candidate pairs (Module 3).

A blocking key is a short value that true pairs usually share (a postcode, the start of the surname). Two records
become a candidate pair when they share a key. Several keys together: a pair is a candidate when it shares any of
them. Sorted neighbourhood: sort the records by a key and pair each record with the next few. MinHash LSH: records
whose sets of shingles are similar land in the same bucket.

Every blocking returns record_id_l < record_id_r, one row per pair; products are paired only across the two feeds.
"""

import time
import zlib

import numpy as np
import pandas as pd

from . import evaluate, prepared
from .pairs import same_value_pairs
from .paths import out

# ---------------------------------------------------------------- keys

def customer_keys(df):
    """The key columns a blocking can use (computed from the prepared customers)."""
    first1, first2 = df["first"].str[:1], df["first"].str[:2]
    last = df["last"].str.replace(" ", "")
    return pd.DataFrame({
        "record_id": df.record_id,
        "postcode": df.postcode,
        "email": df.email,
        "phone": df.phone,
        "surname4": np.where(last != "", last.str[:4] + "|" + first2, ""),
        "surname4_wide": np.where(last != "", last.str[:4] + "|" + first1, ""),
        "dob": np.where(df.dob != "", df.dob + "|" + first1, ""),
        "fsa_surname2": np.where((df.postcode != "") & (df["last"] != ""),
                                 df.postcode.str[:3] + "|" + df["last"].str[:2], ""),
        "street_number": np.where((df.number != "") & (df.street != ""), df.number + "|" + df.street.str[:4], ""),
    })


BLOCKINGS = {
    # name: (dataset, keys or method, description)
    "postcode": ("customers", ["postcode"], "same postcode"),
    "surname": ("customers", ["surname4"], "same first 4 letters of the surname and first 2 of the first name"),
    "surname-wide": ("customers", ["surname4_wide"], ("same first 4 letters of the surname and first letter of the first "
                     "name")),
    "email": ("customers", ["email"], "same email"),
    "phone": ("customers", ["phone"], "same phone"),
    "dob": ("customers", ["dob"], "same date of birth and first letter of the first name"),
    "postcode+surname": ("customers", ["postcode", "surname4"], "postcode, or surname start"),
    "keys": ("customers", ["postcode", "email", "phone", "surname4", "dob"],
             "postcode, email, phone, surname start or date of birth (the default)"),
    "keys+street": ("customers", ["postcode", "email", "phone", "surname4", "dob", "street_number"],
                    "the default keys and the street number with the start of the street"),
    "sorted-name": ("customers", "sorted:full:10", "sorted neighbourhood on the full name, window 10"),
    "sorted-name-50": ("customers", "sorted:full:50", "sorted neighbourhood on the full name, window 50"),
    "keys-wide": ("customers", ["postcode", "email", "phone", "surname4_wide", "dob"],
                  "the default keys with the wider surname key"),
    "embed-nn": ("customers", "embed:10", "each record and its 10 nearest records by embedding (cosine)"),
    "p-brand": ("products", ["brand"], "same brand"),
    "p-minhash": ("products", "minhash:0.5", "MinHash LSH on title shingles (threshold 0.5)"),
    "p-minhash-0.3": ("products", "minhash:0.3", "MinHash LSH on title shingles (threshold 0.3)"),
    "p-minhash+gtin": ("products", "minhash:0.5+gtin", "MinHash LSH (0.5) or the same barcode"),
}
DEFAULT = {"customers": "keys", "products": "p-minhash+gtin"}


def key_pairs(keys, cols):
    parts = [same_value_pairs(keys, c) for c in cols]
    return pd.concat(parts).drop_duplicates(["record_id_l", "record_id_r"]).reset_index(drop=True)


def sorted_neighbourhood(df, col, window):
    """Sort the records by col and pair each record with the next window - 1 records."""
    d = df[df[col] != ""].sort_values([col, "record_id"])
    ids = d.record_id.to_numpy()
    parts = []
    for k in range(1, window):
        a, b = ids[:-k], ids[k:]
        parts.append(pd.DataFrame({"record_id_l": np.minimum(a, b), "record_id_r": np.maximum(a, b)}))
    return pd.concat(parts).drop_duplicates().reset_index(drop=True)


# ---------------------------------------------------------------- MinHash LSH (products)

def shingles(text, k=3):
    """The set of k-letter pieces of a text ('hose' with k = 3: {'hos', 'ose'})."""
    t = " ".join(str(text).split())
    return {t[i:i + k] for i in range(max(1, len(t) - k + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def minhash_signature(sh, n=64, seed=1):
    """n MinHash values for a set of shingles: for each of n hash functions, the smallest hash in the set."""
    rng = np.random.default_rng(seed)
    a = rng.integers(1, 2**31 - 1, size=n, dtype=np.int64)
    b = rng.integers(0, 2**31 - 1, size=n, dtype=np.int64)
    h = np.array([zlib.crc32(s.encode()) for s in sh], dtype=np.int64)
    return ((np.outer(a, h) + b[:, None]) % (2**31 - 1)).min(axis=1)


def lsh_pairs(texts, ids, threshold=0.5, num_perm=128, k=3):
    """Candidate pairs from datasketch's MinHash LSH (records whose signatures share a band)."""
    from datasketch import MinHash, MinHashLSH
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    sigs = {}
    for rid, t in zip(ids, texts):
        m = MinHash(num_perm=num_perm, seed=1)
        m.update_batch([s.encode() for s in shingles(t, k)])
        sigs[rid] = m
        lsh.insert(rid, m)
    rows = set()
    for rid, m in sigs.items():
        for other in lsh.query(m):
            if other != rid:
                rows.add((min(rid, other), max(rid, other)))
    return pd.DataFrame(sorted(rows), columns=["record_id_l", "record_id_r"])


def product_text(df):
    """The text that MinHash and embeddings read for a product: brand and title words, without size and pack."""
    return (df.brand + " " + df.words).str.strip()


# ---------------------------------------------------------------- run a blocking

def candidates(name, rebuild=False):
    """The candidate pairs of a blocking (kept in outputs/candidates/<name>.pkl)."""
    if name not in BLOCKINGS:
        raise SystemExit(f"No blocking called {name!r}. Blockings: {', '.join(BLOCKINGS)}")
    p = out("candidates", f"{name}.pkl")
    if p.exists() and not rebuild:
        return pd.read_pickle(p)
    ds, how, _ = BLOCKINGS[name]
    df = prepared.get(ds)
    if isinstance(how, list):
        keys = customer_keys(df) if ds == "customers" else df[["record_id", "brand", "gtin"]]
        c = key_pairs(keys, how)
    elif how.startswith("embed:"):
        from . import embed
        c = embed.nearest_pairs(ds, k=int(how.split(":")[1]))[["record_id_l", "record_id_r"]]
    elif how.startswith("sorted:"):
        _, col, w = how.split(":")
        c = sorted_neighbourhood(df, col, int(w))
    else:
        spec = how.split(":")[1]
        thr = float(spec.split("+")[0])
        c = lsh_pairs(product_text(df), df.record_id, threshold=thr)
        if spec.endswith("+gtin"):
            c = pd.concat([c, same_value_pairs(df, "gtin")]).drop_duplicates()
    if ds == "products":
        c = c[c.record_id_l.str[:2] != c.record_id_r.str[:2]]
    c = c.reset_index(drop=True)
    c.to_pickle(p)
    return c


def all_pairs(ds):
    n = len(prepared.get(ds))
    if ds == "products":
        df = prepared.get(ds)
        return int((df.feed == "a").sum()) * int((df.feed == "b").sum())
    return n * (n - 1) // 2


def measure(name, rebuild=False):
    """Candidate pairs, pair completeness (share of true pairs kept) and reduction ratio (share of pairs removed)."""
    ds = BLOCKINGS[name][0]
    t0 = time.perf_counter()
    c = candidates(name, rebuild=rebuild)
    secs = time.perf_counter() - t0
    truth = evaluate.true_pairs(ds)
    kept = truth.merge(c, on=["record_id_l", "record_id_r"], how="inner")
    return {"blocking": name, "candidates": len(c), "true_pairs": len(truth), "true_kept": len(kept),
            "pair_completeness": len(kept) / len(truth), "reduction_ratio": 1 - len(c) / all_pairs(ds),
            "all_pairs": all_pairs(ds), "seconds": round(secs, 2)}
