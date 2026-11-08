"""Synonyms (Module 4, lesson 3): rules from data/synonyms.csv, tested one by one.

A two-way rule "couch, sofa" adds "sofa" to a query with "couch" and "couch" to a query with "sofa". A one-way rule
"sectional => sofa" adds "sofa" to a query with "sectional", never the other way. The added words count half
(EXPANSION_WEIGHT): a product with the person's own words still ranks first.
"""

import re
from functools import lru_cache

import pandas as pd

from .normalise import fold
from .paths import data_dir

EXPANSION_WEIGHT = 0.5


def parse(rule):
    """'a, b' -> [({a}, {b}), ({b}, {a})] ; 'a => b' -> [({a}, {b})]"""
    if "=>" in rule:
        left, right = rule.split("=>")
        lhs = [fold(t).strip() for t in left.split(",")]
        rhs = [fold(t).strip() for t in right.split(",")]
        return [(lhs, rhs)]
    terms = [fold(t).strip() for t in rule.split(",")]
    return [([t], [o for o in terms if o != t]) for t in terms]


@lru_cache(maxsize=1)
def rules():
    df = pd.read_csv(data_dir() / "synonyms.csv", keep_default_na=False)
    return [(r.rule, pairs) for r in df.itertuples() for pairs in [parse(r.rule)]]


def expansion(query, only=None, skip=()):
    """The words to add to a query: from every rule, or only from the rule `only`, never from rules in `skip`."""
    q = " " + fold(query) + " "
    use = [(only, parse(only))] if only else [(r, p) for r, p in rules() if r not in skip]
    added = []
    for _, pairs in use:
        for lhs, rhs in pairs:
            if any(re.search(rf"\b{re.escape(t)}\b", q) for t in lhs):
                added += [t for t in rhs if not re.search(rf"\b{re.escape(t)}\b", q)]
    return " ".join(dict.fromkeys(added))


def matches(query, rule):
    q = " " + fold(query) + " "
    return any(re.search(rf"\b{re.escape(t)}\b", q) for lhs, _ in parse(rule) for t in lhs)
