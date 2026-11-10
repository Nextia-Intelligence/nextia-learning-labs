"""Normalise text before matching (Module 4, lesson 1): case, accents, units, then stemming.

    norm("Gray Outdoor Cushions 18''")  -> ['gray', 'outdoor', 'cushion', '18', 'inch']
    norm_fr("Coussins gris extérieurs") -> ['coussin', 'gris', 'exterieur']

Stemming cuts a word to its stem with the Snowball rules (PyStemmer), in English for the English fields and in
French for the French titles. It joins "cushion" and "cushions", and it also joins words that do not mean the same
thing ("light" and "lighting"): measure it.
"""

import re
import unicodedata

import Stemmer

from .text import ANALYZERS, tokens

_EN = Stemmer.Stemmer("english")
_FR = Stemmer.Stemmer("french")
_UNITS = [
    (re.compile(r"(\d)\s*(?:''|\"|”|″|-?inch(?:es)?\b|in\b\.?)"), r"\1 inch "),
    (re.compile(r"(\d)\s*(?:'|ft\b|feet\b|foot\b)"), r"\1 ft "),
    (re.compile(r"(\d)\s*x\s*(\d)"), r"\1 x \2"),
    (re.compile(r"(\d)\s*(cm|mm|qt|lb|lbs|gal)\b"), r"\1 \2"),
    (re.compile(r"\bx(\d)"), r"x \1"),
]


def fold(text):
    """Lower case, no accents, units written one way: 'Café 24”x18' -> 'cafe 24 inch x 18'."""
    t = unicodedata.normalize("NFKD", str(text).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    for pattern, repl in _UNITS:
        t = pattern.sub(repl, t)
    return t


def norm(text):
    return _EN.stemWords(tokens(fold(text)))


def norm_fr(text):
    return _FR.stemWords(tokens(fold(text)))


ANALYZERS["norm"] = norm
ANALYZERS["norm_fr"] = norm_fr
