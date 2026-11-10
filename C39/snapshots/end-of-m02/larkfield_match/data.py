"""Read the course data: Larkfield's three customer sources, the supplier feeds and the true entities.

Every record is synthetic: our code made it from known true people, so we always know the right answer.
"""

import hashlib
import json
from functools import cache

import pandas as pd

from .paths import data_dir

SOURCES = {"shop": "shop_accounts.csv", "loyalty": "loyalty_members.csv", "garden": "garden_centres.csv"}
SOURCE_NAMES = {"shop": "shop accounts", "loyalty": "loyalty members", "garden": "garden centres"}


def _csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


@cache
def source(name):
    """One source as it is: its own columns, every value as text."""
    return _csv(data_dir() / "sources" / SOURCES[name])


def unify(df, name):
    """Puts one source into the shared columns, without cleaning anything.

    name, address and date_of_birth stay exactly as the source wrote them: the shop keeps first and last name
    apart (joined here with a space), the loyalty programme writes one full name and day/month/year dates, the
    garden centres write "SURNAME, FIRST" and the whole address in one field.
    """
    if name == "shop":
        name_ = df.first_name + " " + df.last_name
        address = df.address + ", " + df.city + " " + df.province
        postcode, created = df.postcode, df.created
    elif name == "loyalty":
        name_, address, postcode, created = df.full_name, "", df.postcode, df.joined
    else:
        name_, address, postcode, created = df.name, df.address, "", df.first_visit
    out = pd.DataFrame({"record_id": df.record_id, "source": name, "name": name_, "email": df.email,
                        "phone": df.phone, "address": address, "postcode": postcode,
                        "date_of_birth": df.date_of_birth, "created": created})
    return out


@cache
def records():
    """All customer records in the shared columns (raw values)."""
    return pd.concat([unify(source(s), s) for s in SOURCES], ignore_index=True)


@cache
def truth():
    """record_id -> entity_id and split (train, validation, test), for every customer record."""
    return _csv(data_dir() / "truth.csv")


@cache
def planted():
    """The practice problems we made on purpose: record_id, problem."""
    return _csv(data_dir() / "planted.csv")


@cache
def feed(name):
    """A supplier feed: 'a' (Northfield Supply) or 'b' (Copperleaf Wholesale)."""
    return _csv(data_dir() / "products" / f"feed_{name}.csv")


@cache
def product_truth():
    return _csv(data_dir() / "products" / "truth.csv")


@cache
def product_planted():
    return _csv(data_dir() / "products" / "planted.csv").rename(columns={"product_id": "record_id"})


def dataset_truth(dataset):
    """The truth table of a dataset with the shared columns record_id, entity_id, split."""
    if dataset == "products":
        t = product_truth()
        return pd.DataFrame({"record_id": t.product_id, "entity_id": t.product_entity, "split": t.split})
    return truth()


def labelled_pairs():
    return _csv(data_dir() / "labelled_pairs.csv").astype({"label": int})


def costs():
    return json.loads((data_dir() / "costs.json").read_text())


def expected():
    return json.loads((data_dir() / "expected.json").read_text())


def checksums():
    """name -> SHA-256 from data/SHA256SUMS."""
    out = {}
    for line in (data_dir() / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.strip()] = digest
    return out


def verify():
    """The data files that are missing or changed (an empty list when all are right)."""
    bad = []
    for name, digest in checksums().items():
        p = data_dir() / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(name)
    return bad
