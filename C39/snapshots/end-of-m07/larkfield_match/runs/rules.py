"""Exact keys after normalisation, and rules (Module 2, lesson 3)."""

import pandas as pd

from .. import prepared
from ..pairs import same_value_pairs


def _key_pairs(cols):
    df = prepared.customers()
    keep = (df[cols] != "").all(axis=1)
    d = df[keep].assign(key=df[keep][cols].agg("|".join, axis=1))
    return same_value_pairs(d, "key")


def _union(*frames):
    return pd.concat(frames).drop_duplicates(["record_id_l", "record_id_r"])


def exact_norm():
    return _key_pairs(["email"]).assign(score=1.0, match=1)


def phone_surname():
    return _key_pairs(["phone", "last"]).assign(score=1.0, match=1)


def name_dob():
    return _key_pairs(["first", "last", "dob"]).assign(score=1.0, match=1)


def name_postcode():
    return _key_pairs(["first", "last", "postcode"]).assign(score=1.0, match=1)


def phone_only():
    return _key_pairs(["phone"]).assign(score=1.0, match=1)


def rules():
    return _union(_key_pairs(["email"]), _key_pairs(["phone", "last"]), _key_pairs(["first", "last", "dob"]),
                  _key_pairs(["first", "last", "postcode"])).assign(score=1.0, match=1)


def _cross_feed(p):
    return p[p.record_id_l.str[:2] != p.record_id_r.str[:2]]


def p_gtin():
    df = prepared.products()
    return _cross_feed(same_value_pairs(df, "gtin")).assign(score=1.0, match=1)


def p_title():
    df = prepared.products()
    words = df.words.str.split().map(lambda w: " ".join(sorted(w)))   # word order differs between the feeds
    d = df.assign(key=df.brand + "|" + words + "|" + df["size"].map(lambda v: "" if pd.isna(v) else f"{v:g}") + "|" + df["pack"].astype(str))
    return _cross_feed(same_value_pairs(d, "key")).assign(score=1.0, match=1)


def p_rules():
    return _union(p_gtin(), p_title())


RUNS = {
    "exact-norm": ("customers", exact_norm, "same email after normalising"),
    "rule-phone-surname": ("customers", phone_surname, "same phone and same surname"),
    "rule-name-dob": ("customers", name_dob, "same first name, surname and date of birth"),
    "rule-name-postcode": ("customers", name_postcode, "same first name, surname and postcode"),
    "rule-phone": ("customers", phone_only, "same phone (and nothing else)"),
    "rules": ("customers", rules, "same email, or phone and surname, or name and birth date, or name and postcode"),
    "p-gtin": ("products", p_gtin, "same barcode (GTIN) when both feeds have one"),
    "p-title": ("products", p_title, "same brand, title words, size and pack after parsing"),
    "p-rules": ("products", p_rules, "same barcode, or same parsed title"),
}
