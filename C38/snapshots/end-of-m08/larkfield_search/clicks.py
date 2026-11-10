"""The click model: how the synthetic query log was made, and how to learn from clicks.

The query log of the course is synthetic. Our code made every click with this position-based click model:

    a person looks at the result at position k with probability  examine(k) = 1 / k ** ETA     (ETA = 1.0)
    if they look, they click with probability                     CLICK[grade]
    after a click, they add the product to the cart with          CART[grade]

grade is the judgment of the product for the query (2 exact, 1 partial, 0 irrelevant; a product with no judgment
counts as 0). The numbers are assumptions that we chose, not measurements of real people. Real click logs have
the same shape (people look at the top far more), but the numbers differ from shop to shop.

Module 6 uses the same functions to learn from clicks: the clicks of a product depend on its position as well as
on its relevance, so a click is weak evidence. Dividing by examine(k) (inverse propensity weighting) removes the
position part when ETA is known.
"""

import numpy as np

ETA = 1.0
CLICK = {2: 0.65, 1: 0.25, 0: 0.05}
CART = {2: 0.30, 1: 0.08, 0: 0.01}
PAGE = 10


def examine(position, eta=ETA):
    """The chance that a person looks at the result at this position (1 = top)."""
    return 1.0 / np.asarray(position, dtype=float) ** eta


def simulate(ranked, judged, rng, eta=ETA):
    """Clicks and add-to-cart (two lists of 0/1) for one page of results shown to one person."""
    clicks, carts = [], []
    for k, pid in enumerate(ranked[:PAGE], 1):
        g = judged.get(pid, 0)
        c = rng.random() < examine(k, eta) * CLICK[g]
        a = c and rng.random() < CART[g]
        clicks.append(int(c))
        carts.append(int(a))
    return clicks, carts


def ctr_by_position(impressions):
    """Click-through rate at each position of a DataFrame with columns position and clicked."""
    return impressions.groupby("position")["clicked"].mean()


def propensity(impressions, grades):
    """Estimate examine(k) from the log: the click rate of exact products at position k divided by the rate at 1.

    impressions needs columns position, clicked and grade (the judgment of the product for the search's query).
    Only exact products are used, so relevance is the same at every position and the rest is position.
    """
    ex = impressions[impressions["grade"] == 2]
    rate = ex.groupby("position")["clicked"].mean()
    return (rate / rate.loc[1]).rename("estimated examine(k)")


def click_labels(impressions, eta=None):
    """Labels for learning to rank from clicks: one row per (query, product) shown.

    Without eta: the share of times it was clicked when shown (naive). With eta: each click is divided by the
    chance that the person looked at its position (inverse propensity weighting), so a click at position 8 counts
    more than a click at position 1.
    """
    df = impressions.copy()
    weight = 1.0 if eta is None else 1.0 / examine(df["position"], eta)
    df["w_click"] = df["clicked"] * weight
    out = df.groupby(["query", "product_id"]).agg(shown=("clicked", "size"), clicks=("clicked", "sum"),
                                                  w_clicks=("w_click", "sum"),
                                                  best_position=("position", "min")).reset_index()
    out["label"] = out["w_clicks"] / out["shown"]
    return out
