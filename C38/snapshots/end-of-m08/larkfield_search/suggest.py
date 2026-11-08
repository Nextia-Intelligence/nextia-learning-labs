"""Autocomplete (Module 7, lesson 1): suggestions from the query log and the catalogue with a prefix index.

A suggestion is a past query that got at least one click (weight: the number of such searches) or a product
class name (weight: 1 for each 20 products of the class). Suggestions that only ever returned nothing, and
suggestions with a word the spelling checker would change, are removed. The prefix index is a sorted list:
every suggestion that starts with what the person typed is next to the others, so a binary search finds them.
"""

import bisect
import json
from collections import Counter
from functools import lru_cache

from . import data
from .normalise import fold
from .paths import outputs_dir
from .spell import correct_word
from .text import tokens


@lru_cache(maxsize=1)
def suggestions():
    path = outputs_dir() / "suggestions.json"
    if path.exists():
        return json.loads(path.read_text())
    s = data.searches()
    good = Counter(fold(q).strip() for q in s.loc[s["clicks"] > 0, "query"])
    zero = set(s.groupby("query")["results"].max().loc[lambda x: x == 0].index.map(lambda q: fold(q).strip()))
    w = Counter()
    for q, n in good.items():
        if q in zero or any(correct_word(t)[1] == "corrected" for t in tokens(q)):
            continue
        w[q] += n
    for cls, n in data.catalogue()["product_class"].value_counts().items():
        w[fold(cls)] += max(1, n // 20)
    items = sorted(w.items())
    path.write_text(json.dumps(items))
    return items


def suggest(prefix, n=8):
    """The n best suggestions that start with the prefix: [(text, weight)]."""
    items = suggestions()
    keys = [t for t, _ in items]
    p = fold(prefix).lstrip()
    i = bisect.bisect_left(keys, p)
    found = []
    while i < len(keys) and keys[i].startswith(p):
        found.append(items[i])
        i += 1
    return sorted(found, key=lambda x: (-x[1], x[0]))[:n]
