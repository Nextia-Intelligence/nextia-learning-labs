"""Detect what the query asks for (Module 4, lesson 4): a price limit, a colour, and the product class.

Rules find a price limit ("under 50 dollars", "moins de 50 $") and colour words. A small classifier (Complement
Naive Bayes on the words of the product titles, trained on the catalogue: every product is an example of its
class) guesses the product class of a query. Its guess becomes a boost for products of that class, and the
price limit becomes a filter.
"""

import pickle
import re
from functools import lru_cache

import numpy as np

from . import data
from .normalise import fold
from .paths import outputs_dir
from .text import tokens

PRICE = re.compile(r"(?:under|below|less than|max|cheaper than|moins de|sous)\s*\$?\s*(\d+(?:\.\d+)?)\s*"
                   r"(?:\$|dollars?|cad)?", re.IGNORECASE)
COLOURS = {"black", "white", "grey", "gray", "blue", "navy", "green", "red", "pink", "yellow", "orange", "purple",
           "brown", "beige", "gold", "silver", "bronze", "teal", "ivory", "cream", "tan", "natural", "turquoise",
           "noir", "blanc", "gris", "bleu", "vert", "rouge", "rose", "jaune", "brun", "dore", "argent"}


@lru_cache(maxsize=1)
def classifier():
    from . import torch_first
    torch_first()
    path = outputs_dir() / "class_classifier.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    from . import torch_first
    torch_first()
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.naive_bayes import ComplementNB
    cat = data.catalogue()
    texts = (cat["title"] + " " + cat["title_fr"] + " " + cat["product_class"]).map(fold)
    vec = CountVectorizer(tokenizer=tokens, token_pattern=None, ngram_range=(1, 2), min_df=2)
    x = vec.fit_transform(texts)
    model = ComplementNB(alpha=0.3).fit(x, cat["product_class"])
    path.write_bytes(pickle.dumps((vec, model)))
    return vec, model


def detect(query, min_share=0.5):
    """{'price_max': float or None, 'colours': [...], 'classes': [...], 'clean': query without the price words}."""
    q = fold(query)
    m = PRICE.search(q)
    price_max = float(m.group(1)) if m else None
    clean = PRICE.sub(" ", q).strip() if m else q
    colours = [w for w in tokens(clean) if w in COLOURS]
    vec, model = classifier()
    p = model.predict_proba(vec.transform([clean]))[0]
    order = np.argsort(-p)
    # Complement NB probabilities are flat: keep the classes within min_share of the best one's score.
    best = p[order[0]]
    classes = [model.classes_[i] for i in order[:3] if p[i] >= best * (1 - min_share) and p[i] > 2 / len(p)]
    return {"price_max": price_max, "colours": colours, "classes": classes, "clean": clean}
