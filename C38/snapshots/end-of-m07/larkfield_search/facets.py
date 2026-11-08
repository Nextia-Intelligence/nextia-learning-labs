"""Filters and facets (Module 7, lesson 2): counts per value in the results, so a filter never returns zero."""

import pandas as pd

from . import data

PRICE_BANDS = [(0, 50, "under 50"), (50, 100, "50 to 100"), (100, 250, "100 to 250"), (250, 500, "250 to 500"),
               (500, 1e9, "500 and more")]


def price_band(price):
    for lo, hi, name in PRICE_BANDS:
        if lo <= price < hi:
            return name
    return PRICE_BANDS[-1][2]


def facets(product_ids, top=6):
    """{facet: [(value, count)]} for the products of a result list; only values that the results have."""
    cat = data.catalogue().set_index("product_id").loc[list(product_ids)]
    colour = cat["colour"].str.split("/").str[0].str.strip().replace("", pd.NA).dropna()
    return {
        "product class": list(cat["product_class"].value_counts().head(top).items()),
        "colour": list(colour.value_counts().head(top).items()),
        "price": [(name, int(n)) for name, n in cat["price"].map(price_band).value_counts()
                  .reindex([b[2] for b in PRICE_BANDS]).dropna().astype(int).items() if n > 0],
        "availability": [("in stock", int(cat["in_stock"].sum())), ("out of stock", int((~cat["in_stock"]).sum()))],
    }


def apply(product_ids, **filters):
    """Keep the products that match every filter: product_class=..., colour=..., price=..., in_stock=True."""
    cat = data.catalogue().set_index("product_id")
    out = []
    for p in product_ids:
        r = cat.loc[p]
        if "product_class" in filters and r["product_class"] != filters["product_class"]:
            continue
        if "colour" in filters and not r["colour"].startswith(filters["colour"]):
            continue
        if "price" in filters and price_band(r["price"]) != filters["price"]:
            continue
        if filters.get("in_stock") and not r["in_stock"]:
            continue
        out.append(p)
    return out
