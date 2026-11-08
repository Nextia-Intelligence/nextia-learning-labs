"""Fix spelling (Module 4, lesson 2): edit distance and a dictionary from the catalogue and the query log.

A word is checked when it has 4 letters or more and is not in the dictionary. The candidates are the dictionary
words one edit away (delete, swap two letters, change or add one letter); if there is none, two edits away (for
words of 7 letters or more). The most frequent candidate wins. The dictionary counts each word in the titles,
classes, categories, attributes and French titles, plus the words of logged searches that got a click.
"""

import json
import string
from collections import Counter
from functools import lru_cache

from . import data
from .normalise import fold
from .paths import outputs_dir
from .text import tokens

LETTERS = string.ascii_lowercase


@lru_cache(maxsize=1)
def dictionary():
    path = outputs_dir() / "spell_dictionary.json"
    if path.exists():
        return Counter(json.loads(path.read_text()))
    c = Counter()
    cat = data.catalogue()
    for col in ("title", "product_class", "category", "attributes", "title_fr"):
        for t in cat[col]:
            c.update(tokens(fold(t)))
    s = data.searches()
    for q in s.loc[s["clicks"] > 0, "query"]:
        c.update(tokens(fold(q)))
    path.write_text(json.dumps(c))
    return c


def edits1(w):
    splits = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    return ({a + b[1:] for a, b in splits if b} | {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1}
            | {a + c + b[1:] for a, b in splits if b for c in LETTERS} | {a + c + b for a, b in splits for c in LETTERS})


def correct_word(w):
    """(word, how): how is 'known', 'corrected' (1 or 2 edits) or 'unknown' (no candidate)."""
    d = dictionary()
    if not w.isalpha() or len(w) < 4 or d.get(w, 0) > 0:
        return w, "known"
    cands = [c for c in edits1(w) if c in d]
    if not cands and len(w) >= 7:
        cands = [c2 for c1 in edits1(w) for c2 in edits1(c1) if c2 in d]
    if not cands:
        return w, "unknown"
    return max(cands, key=lambda c: (d[c], c)), "corrected"


def correct(query):
    """(corrected query, [(word, correction)]) for a query text."""
    words = tokens(fold(query))
    out, changes = [], []
    for w in words:
        c, how = correct_word(w)
        out.append(c)
        if how == "corrected":
            changes.append((w, c))
    return " ".join(out), changes
