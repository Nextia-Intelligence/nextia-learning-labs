"""Comparison vectors: one row of field similarities for each candidate pair (Module 4, lesson 3).

A value is NaN when one of the two records has no value for the field (missing is not the same as different).
"""

import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler
from rapidfuzz.process import cpdist

from . import blocking, prepared
from .paths import out
from .similarity import metaphone

CUSTOMER_FIELDS = ["first_jw", "last_jw", "name_tsr", "first_initial", "last_sound", "email_eq", "email_local_jw",
                   "phone_eq", "postcode_eq", "postcode3_eq", "street_tsr", "number_eq", "town_eq", "dob_eq",
                   "dob_swap", "dob_year_eq"]
PRODUCT_FIELDS = ["title_tsr", "title_jw", "brand_eq", "size_kind_eq", "size_ratio", "pack_eq", "price_ratio",
                  "gtin_eq", "jaccard3"]


def _both(a, b):
    return (a != "") & (b != "")


def _sim(a, b, scorer, scale=1.0):
    return cpdist(a.tolist(), b.tolist(), scorer=scorer, workers=1).astype("float32") / scale


def _eq(a, b):
    v = (a.to_numpy() == b.to_numpy()).astype("float32")
    v[~_both(a, b).to_numpy()] = np.nan
    return v


def _masked(v, a, b):
    v = np.asarray(v, dtype="float32").copy()
    v[~_both(a, b).to_numpy()] = np.nan
    return v


def customer_vectors(pairs, records=None):
    """Field similarities for customer pairs (record_id_l, record_id_r); records: the prepared table to read
    (default: the prepared customers of the course data)."""
    df = (prepared.customers() if records is None else records).set_index("record_id")
    df = df.assign(sound=df["last"].map(metaphone), local=df.email.str.split("@").str[0].fillna(""))
    L = df.loc[pairs.record_id_l].reset_index(drop=True)
    R = df.loc[pairs.record_id_r].reset_index(drop=True)
    v = pd.DataFrame({"record_id_l": pairs.record_id_l.to_numpy(), "record_id_r": pairs.record_id_r.to_numpy()})
    v["first_jw"] = _masked(_sim(L["first"], R["first"], JaroWinkler.similarity), L["first"], R["first"])
    v["last_jw"] = _masked(_sim(L["last"], R["last"], JaroWinkler.similarity), L["last"], R["last"])
    v["name_tsr"] = _masked(_sim(L.full, R.full, fuzz.token_set_ratio, 100), L.full, R.full)
    v["first_initial"] = _eq(L["first"].str[:1], R["first"].str[:1])
    v["last_sound"] = _eq(L.sound, R.sound)
    v["email_eq"] = _eq(L.email, R.email)
    v["email_local_jw"] = _masked(_sim(L.local, R.local, JaroWinkler.similarity), L.local, R.local)
    v["phone_eq"] = _eq(L.phone, R.phone)
    v["postcode_eq"] = _eq(L.postcode, R.postcode)
    v["postcode3_eq"] = _eq(L.postcode.str[:3], R.postcode.str[:3])
    v["street_tsr"] = _masked(_sim(L.street, R.street, fuzz.token_set_ratio, 100), L.street, R.street)
    v["number_eq"] = _eq(L.number, R.number)
    v["town_eq"] = _eq(L.town, R.town)
    v["dob_eq"] = _eq(L.dob, R.dob)
    swapped = R.dob.str[:4] + "-" + R.dob.str[8:10] + "-" + R.dob.str[5:7]
    v["dob_swap"] = _eq(L.dob, swapped.where(R.dob != "", ""))
    v["dob_year_eq"] = _eq(L.dob.str[:4], R.dob.str[:4])
    return v


def product_vectors(pairs):
    df = prepared.products().set_index("record_id")
    df = df.assign(text=blocking.product_text(df.reset_index()).to_numpy(),
                   size_s=df["size"].map(lambda x: "" if pd.isna(x) else f"{x:g}"),
                   pack_s=df["pack"].astype(str))
    L = df.loc[pairs.record_id_l].reset_index(drop=True)
    R = df.loc[pairs.record_id_r].reset_index(drop=True)
    v = pd.DataFrame({"record_id_l": pairs.record_id_l.to_numpy(), "record_id_r": pairs.record_id_r.to_numpy()})
    v["title_tsr"] = _sim(L.text, R.text, fuzz.token_set_ratio, 100)
    v["title_jw"] = _sim(L.text, R.text, JaroWinkler.similarity)
    v["brand_eq"] = _eq(L.brand, R.brand)
    v["size_kind_eq"] = _eq(L.size_kind, R.size_kind)
    ls, rs = L["size"].to_numpy(dtype=float), R["size"].to_numpy(dtype=float)
    v["size_ratio"] = (np.minimum(ls, rs) / np.maximum(ls, rs)).astype("float32")
    v["pack_eq"] = (L["pack"].to_numpy() == R["pack"].to_numpy()).astype("float32")
    lp, rp = L.price.to_numpy(dtype=float), R.price.to_numpy(dtype=float)
    v["price_ratio"] = (np.minimum(lp, rp) / np.maximum(lp, rp)).astype("float32")
    v["gtin_eq"] = _eq(L.gtin, R.gtin)
    v["jaccard3"] = np.array([blocking.jaccard(blocking.shingles(a), blocking.shingles(b))
                              for a, b in zip(L.text, R.text)], dtype="float32")
    return v


def for_pairs(pairs, dataset):
    return product_vectors(pairs) if dataset == "products" else customer_vectors(pairs)


def get(blocking_name, rebuild=False):
    """The comparison vectors of every candidate pair of a blocking (kept in outputs/vectors/)."""
    p = out("vectors", f"{blocking_name}.pkl")
    if p.exists() and not rebuild:
        return pd.read_pickle(p)
    ds = blocking.BLOCKINGS[blocking_name][0]
    v = for_pairs(blocking.candidates(blocking_name), ds)
    v.to_pickle(p)
    return v


def fields(dataset):
    return PRODUCT_FIELDS if dataset == "products" else CUSTOMER_FIELDS
