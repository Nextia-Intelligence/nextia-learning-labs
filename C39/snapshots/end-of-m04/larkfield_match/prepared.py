"""The prepared records: every source parsed and normalised into one table (kept in outputs/prepared_*.pkl).

Customers: record_id, source, first, last, full, email, phone, number, street, unit, town, province, postcode,
dob, created, parse_ok. Products: record_id, feed, title, words, brand, size, size_kind, pack, gtin, price.
"""

import pandas as pd

from . import data
from . import normalise as nz
from .parse import parse_title, split_address, split_name
from .paths import out

CUSTOMER_COLUMNS = ["record_id", "source", "first", "last", "full", "email", "phone", "number", "street", "unit",
                    "town", "province", "postcode", "dob", "created", "parse_ok"]


def prepare_source(df, name):
    """One source (its own columns) -> the prepared columns."""
    rows = []
    for r in df.to_dict("records"):
        if name == "shop":
            nm = {"first": nz.name(r["first_name"]), "last": nz.name(r["last_name"])}
            nm["ok"] = bool(nm["first"] and nm["last"])
            ad = split_address(f"{r['address']}, {r['city']} {r['province']} {r['postcode']}")
        elif name == "loyalty":
            nm = split_name(r["full_name"])
            ad = {"number": "", "street": "", "unit": "", "town": "", "province": "",
                  "postcode": nz.postcode(r["postcode"]), "ok": True}
        else:
            nm = split_name(r["name"])
            ad = split_address(r["address"])
        rows.append({
            "record_id": r["record_id"], "source": name, "first": nm["first"], "last": nm["last"],
            "full": f"{nm['first']} {nm['last']}".strip(), "email": nz.email(r.get("email", "")),
            "phone": nz.phone(r.get("phone", "")), "number": ad["number"], "street": ad["street"],
            "unit": ad["unit"], "town": ad["town"], "province": ad["province"],
            "postcode": nz.postcode(ad["postcode"]), "dob": nz.date(r.get("date_of_birth", "")),
            "created": r.get("created") or r.get("joined") or r.get("first_visit") or "",
            "parse_ok": bool(nm["ok"] and ad["ok"]),
        })
    return pd.DataFrame(rows, columns=CUSTOMER_COLUMNS)


def customers(rebuild=False):
    p = out("prepared_customers.pkl")
    if p.exists() and not rebuild:
        return pd.read_pickle(p)
    df = pd.concat([prepare_source(data.source(s), s) for s in data.SOURCES], ignore_index=True)
    df.to_pickle(p)
    return df


def prepare_feed(df, name):
    rows = []
    for r in df.to_dict("records"):
        t = parse_title(r["title"])
        brand = r.get("brand") or r.get("supplier_brand") or ""
        words = " ".join(w for w in t["words"].split() if w not in nz.text(brand).split())
        rows.append({"record_id": r["product_id"], "feed": name, "title": r["title"], "words": words,
                     "brand": nz.text(brand), "size": t["size"], "size_kind": t["size_kind"], "pack": t["pack"],
                     "gtin": str(r.get("gtin") or ""), "price": float(r["price"])})
    return pd.DataFrame(rows)


def products(rebuild=False):
    p = out("prepared_products.pkl")
    if p.exists() and not rebuild:
        return pd.read_pickle(p)
    df = pd.concat([prepare_feed(data.feed("a"), "a"), prepare_feed(data.feed("b"), "b")], ignore_index=True)
    df.to_pickle(p)
    return df


def get(dataset):
    return products() if dataset == "products" else customers()
