"""Run a matcher and keep its pairs in outputs/runs/<name>.pkl, so later commands do not run it again."""

import time

import pandas as pd

from . import data, runs
from .paths import out

COLUMNS = ["record_id_l", "record_id_r", "score", "match"]


def path(name):
    return out("runs", f"{name.replace('/', '_')}.pkl")


def dataset(name):
    return runs.get(name)[0]


def record_ids(dataset_name):
    return data.dataset_truth(dataset_name).record_id.tolist()


def get(name, rebuild=False, quiet=False):
    """The pairs of a run (computed the first time, then read from outputs/)."""
    p = path(name)
    if p.exists() and not rebuild:
        return pd.read_pickle(p)
    _, fn, _ = runs.get(name)
    t0 = time.perf_counter()
    df = fn()
    df = df[COLUMNS].reset_index(drop=True)
    df["match"] = df["match"].astype(int)
    df.to_pickle(p)
    if not quiet:
        print(f"Ran {name}: {int(df['match'].sum()):,} pairs called the same, in {time.perf_counter() - t0:.1f} s")
    return df


def same_value_pairs(df, key_col, id_col="record_id"):
    """Every pair of records that share a non-empty value of key_col (record_id_l < record_id_r)."""
    d = df[df[key_col].notna() & (df[key_col] != "")][[id_col, key_col]]
    m = d.merge(d, on=key_col, suffixes=("_l", "_r"))
    m = m[m[f"{id_col}_l"] < m[f"{id_col}_r"]]
    return m.rename(columns={f"{id_col}_l": "record_id_l", f"{id_col}_r": "record_id_r"})[
        ["record_id_l", "record_id_r"]].drop_duplicates()
