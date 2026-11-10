"""Privacy and matching (Module 8, lesson 4): match on hashed or encoded values instead of raw ones.

- Hashing (HMAC-SHA-256 with a secret key): equal values give equal codes, so exact rules still work; a single
  typo gives a completely different code, so fuzzy matching is impossible.
- Bloom filter encoding: the letter pairs (bigrams) of a value are hashed into a row of 1,000 bits. Similar
  values share many bits, so the Dice coefficient of two rows behaves like a string similarity.
- Known weakness: equal values still give equal rows. Count the rows: the most frequent ones are the most
  common names, and anyone with a list of common names can guess them (a frequency attack).

The key below is a practice key made for the course. In a real project, the key is a secret that only the
data owners share, and it is never stored with the data.
"""

import hashlib
import hmac

import numpy as np
import pandas as pd

from . import prepared

PRACTICE_KEY = b"larkfield-course-practice-key"
BITS = 1000
HASHES = 20


def hashed(value, key=PRACTICE_KEY):
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:16] if value else ""


def bigrams(value):
    v = f"_{value}_"
    return {v[i:i + 2] for i in range(len(v) - 1)}


def bloom(value, key=PRACTICE_KEY, bits=BITS, k=HASHES):
    """The set bit positions of a value's Bloom filter (double hashing of each bigram)."""
    out = set()
    for g in bigrams(value) if value else ():
        h1 = int.from_bytes(hmac.new(key, b"1" + g.encode(), hashlib.sha256).digest()[:8], "big")
        h2 = int.from_bytes(hmac.new(key, b"2" + g.encode(), hashlib.sha256).digest()[:8], "big")
        out.update((h1 + i * h2) % bits for i in range(k))
    return frozenset(out)


def dice(a, b):
    """2 x shared bits / (bits in a + bits in b); NaN when one value is missing."""
    if not a or not b:
        return float("nan")
    return 2 * len(a & b) / (len(a) + len(b))


def encode(df=None):
    """Each record with only encoded values: Bloom filters of first name, surname and street; hashes of email,
    phone, postcode and date of birth. No raw value is kept."""
    df = prepared.customers() if df is None else df
    cache = {}

    def bf(v):
        if v not in cache:
            cache[v] = bloom(v)
        return cache[v]
    return pd.DataFrame({
        "record_id": df.record_id,
        "first_bf": [bf(v) for v in df["first"]], "last_bf": [bf(v) for v in df["last"]],
        "street_bf": [bf(f"{n} {s}".strip()) for n, s in zip(df.number, df.street)],
        "email_h": [hashed(v) for v in df.email], "phone_h": [hashed(v) for v in df.phone],
        "postcode_h": [hashed(v) for v in df.postcode], "dob_h": [hashed(v) for v in df.dob],
    })


ENCODED_FIELDS = ["first_dice", "last_dice", "street_dice", "email_eq", "phone_eq", "postcode_eq", "dob_eq"]


def encoded_vectors(pairs, enc):
    e = enc.set_index("record_id")
    L, R = e.loc[pairs.record_id_l].reset_index(drop=True), e.loc[pairs.record_id_r].reset_index(drop=True)
    v = pairs[["record_id_l", "record_id_r"]].reset_index(drop=True).copy()
    for f in ("first", "last", "street"):
        v[f"{f}_dice"] = np.array([dice(a, b) for a, b in zip(L[f"{f}_bf"], R[f"{f}_bf"])], dtype="float32")
    for f in ("email", "phone", "postcode", "dob"):
        a, b = L[f"{f}_h"].to_numpy(), R[f"{f}_h"].to_numpy()
        x = (a == b).astype("float32")
        x[(a == "") | (b == "")] = np.nan
        v[f"{f}_eq"] = x
    return v


def frequency_attack(enc, public_names, column="last_bf", top=10):
    """Rank the encoded surnames by how often they occur, and guess that the n-th most frequent is the n-th most
    common surname of a public list. Returns the guesses."""
    counts = enc[column][enc[column].map(len) > 0].value_counts().head(top)
    return [(i + 1, int(n), public_names[i] if i < len(public_names) else "") for i, n in enumerate(counts.values)], \
        list(counts.index)
