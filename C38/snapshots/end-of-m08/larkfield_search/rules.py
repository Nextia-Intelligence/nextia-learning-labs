"""Exact-match rules (Module 3, lesson 3): a product code in the query finds that product directly.

Larkfield's product codes are LK- and five digits. People type them in many ways: "LK-48213", "lk48213",
"lk 48213" or only "48213". A word-by-word search cannot match them, because the index has no such word.
"""

import re
from functools import lru_cache

from . import data

CODE = re.compile(r"\b(?:lk[\s-]?)?(\d{5})\b", re.IGNORECASE)


@lru_cache(maxsize=1)
def known_ids():
    return frozenset(data.catalogue()["product_id"])


def code_matches(query, ids=False):
    """[(product_id, score)] of the products whose code is in the query (score 1,000,000: always first)."""
    known = known_ids()
    found = []
    for m in CODE.finditer(query):
        pid = f"LK-{m.group(1)}"
        if pid in known and pid not in found:
            found.append(pid)
    return set(found) if ids else [(p, 1e6) for p in found]


def with_codes(query, results, k=100):
    """Put the products whose code is in the query first, then the other results."""
    first = code_matches(query)
    if not first:
        return results[:k]
    taken = {p for p, _ in first}
    return (first + [r for r in results if r[0] not in taken])[:k]
