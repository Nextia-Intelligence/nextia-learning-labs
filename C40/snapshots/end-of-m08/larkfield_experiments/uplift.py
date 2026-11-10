"""Uplift: who should get the treatment? Models that predict, for each customer, how much the email changes their
chance to order (not the chance itself), and the uplift and Qini curves that evaluate them.

The T-learner and X-learner come from EconML (Microsoft, MIT licence); the base models from scikit-learn."""

import numpy as np
import pandas as pd

FEATURES = ["new_customer", "tenure_days", "orders_12m", "spend_12m", "days_since_order", "email_open_rate", "mobile"]


def features(df: pd.DataFrame) -> np.ndarray:
    return df.assign(mobile=(df["device"] == "mobile").astype(int))[FEATURES].to_numpy(float)


def _regressor():
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=100,
                                         random_state=0)


def fit_scores(train: pd.DataFrame, score_on: list, learner: str):
    """Fits a learner on the randomised test and returns its scores for each frame in score_on.

    'response' is the usual "who will buy" model: trained on the emailed customers only, it scores the chance to
    order when emailed. 't' and 'x' are uplift models: they score the change the email makes."""
    from threadpoolctl import threadpool_limits

    x, y, t = features(train), train["ordered"].to_numpy(float), (train["variant"] == "B").to_numpy(int)
    with threadpool_limits(1):
        if learner == "response":
            from sklearn.ensemble import HistGradientBoostingClassifier
            m = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_leaf_nodes=15,
                                               min_samples_leaf=100, random_state=0).fit(x[t == 1], y[t == 1])
            return [m.predict_proba(features(f))[:, 1] for f in score_on]
        from econml.metalearners import TLearner, XLearner
        if learner == "t":
            m = TLearner(models=_regressor())
        else:
            from sklearn.linear_model import LogisticRegression
            m = XLearner(models=_regressor(), propensity_model=LogisticRegression(max_iter=1000))
        m.fit(y, t, X=x)
        return [m.effect(features(f)) for f in score_on]


def uplift_curve(score, y, t, points=20):
    """Sort by score (best first). At each cut, the extra orders = treated orders − control orders × (treated /
    control count) among the customers above the cut, scaled to the whole group. Returns (shares, extra orders)."""
    order = np.argsort(-score)
    y, t = y[order], t[order]
    n = len(y)
    shares, gains = [0.0], [0.0]
    for k in np.linspace(n / points, n, points).astype(int):
        yt, yc, nt, nc = y[:k][t[:k] == 1].sum(), y[:k][t[:k] == 0].sum(), (t[:k] == 1).sum(), (t[:k] == 0).sum()
        gain = (yt / max(nt, 1) - yc / max(nc, 1)) * k
        shares.append(k / n)
        gains.append(float(gain))
    return np.array(shares), np.array(gains)


def qini_coefficient(shares, gains):
    """The area between the model's curve and the straight line of random targeting (higher is better)."""
    random = gains[-1] * shares
    return float(np.trapezoid(gains - random, shares))
