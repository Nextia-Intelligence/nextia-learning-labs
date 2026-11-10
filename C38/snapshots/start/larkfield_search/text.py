"""Turn text into tokens.

`tokens` is the plain way: lower case, split on everything that is not a letter or a digit. Module 4 adds a
second way (normalise.py) and registers it in ANALYZERS, so the index and the runs can use either.
"""

import re

_SPLIT = re.compile(r"[^\w]+|_")


def tokens(text):
    """'Grey Outdoor Cushion, 18"' -> ['grey', 'outdoor', 'cushion', '18']"""
    return [t for t in _SPLIT.split(str(text).lower()) if t]


# name -> function(text) -> list of tokens. normalise.py adds "norm".
ANALYZERS = {"plain": tokens}
