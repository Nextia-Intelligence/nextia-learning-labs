"""How alike are two values? String and phonetic measures (Module 4).

Every measure returns a number from 0 (nothing alike) to 1 (the same).
"""

import jellyfish
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler, Levenshtein

from .normalise import strip_accents


def levenshtein_distance(a, b):
    """The smallest number of one-letter changes (insert, delete, replace) that turn a into b. Written out so you
    can follow it; rapidfuzz computes the same number much faster."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def levenshtein(a, b):
    """1 - distance / length of the longer value."""
    return Levenshtein.normalized_similarity(a, b)


def jaro_winkler(a, b):
    """Counts letters in common near the same place, and gives extra credit to a shared start."""
    return JaroWinkler.similarity(a, b)


def token_set_ratio(a, b):
    """Compares the sets of words, so word order and extra words matter less ('bob smith' / 'smith bob' = 1)."""
    return fuzz.token_set_ratio(a, b) / 100


def soundex(s):
    """A 4-character sound code ('Robert' and 'Rupert' -> R163). Made for English names."""
    s = strip_accents(s)
    return jellyfish.soundex(s) if s else ""


def metaphone(s):
    """A sound code with more English spelling rules ('Thompson' -> 0MPSN: 0 is the 'th' of 'thin')."""
    s = strip_accents(s)
    return jellyfish.metaphone(s) if s else ""


MEASURES = {"levenshtein": levenshtein, "jaro_winkler": jaro_winkler, "token_set_ratio": token_set_ratio}
CODES = {"soundex": soundex, "metaphone": metaphone}
