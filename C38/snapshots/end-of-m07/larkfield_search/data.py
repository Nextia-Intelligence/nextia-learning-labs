"""Read the course data: the catalogue, the queries, the judgments and the synthetic query log."""

import hashlib
from functools import lru_cache

import pandas as pd

from .paths import data_dir


@lru_cache(maxsize=1)
def catalogue() -> pd.DataFrame:
    """One row per product: product_id, title, product_class, category, description, attributes, colour, style,
    material, price, on_sale, in_stock, added, ratings, title_fr (empty when there is no French title)."""
    df = pd.read_csv(data_dir() / "catalogue.csv.gz", dtype={"title_fr": str}, keep_default_na=False,
                     na_values={"average_rating": [""]})
    for col in ("on_sale", "in_stock"):
        df[col] = df[col].astype(str).eq("True")
    return df


@lru_cache(maxsize=1)
def queries() -> pd.DataFrame:
    """One row per query: query_id, query, language, split, source, base_query_id, query_class, qtype, band,
    has_number, planted."""
    df = pd.read_csv(data_dir() / "queries.csv", keep_default_na=False)
    for col in ("has_number", "planted"):
        df[col] = df[col].astype(str).eq("True")
    return df


@lru_cache(maxsize=1)
def judgments() -> dict:
    """{query_id: {product_id: grade}} with grade 2 exact, 1 partial, 0 irrelevant."""
    df = pd.read_csv(data_dir() / "judgments.csv.gz")
    out = {}
    for qid, pid, grade in zip(df["query_id"], df["product_id"], df["grade"]):
        out.setdefault(qid, {})[pid] = int(grade)
    return out


@lru_cache(maxsize=1)
def searches() -> pd.DataFrame:
    """The synthetic query log, one row per search."""
    return pd.read_csv(data_dir() / "log" / "searches.csv.gz", keep_default_na=False)


@lru_cache(maxsize=1)
def impressions() -> pd.DataFrame:
    """The synthetic query log, one row per product shown: search_id, position, product_id, clicked, added_to_cart."""
    return pd.read_csv(data_dir() / "log" / "impressions.csv.gz")


def split(name):
    """The queries of one split ('train', 'validation' or 'test'), in order."""
    q = queries()
    return q[q["split"] == name].reset_index(drop=True)


def checksums():
    """{file: sha256} from data/SHA256SUMS."""
    out = {}
    for line in (data_dir() / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            h, name = line.split(maxsplit=1)
            out[name.strip()] = h
    return out


def verify():
    """Names of the data files that are missing or changed."""
    bad = []
    for name, h in checksums().items():
        p = data_dir() / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
            bad.append(name)
    return bad
