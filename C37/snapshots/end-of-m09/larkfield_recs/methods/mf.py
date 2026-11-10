"""Matrix factorisation for implicit feedback with the implicit library: ALS and BPR.

Each customer and each product gets a vector of `factors` numbers (hidden tastes). The score of a product for a
customer is the dot product of their vectors. ALS fits the weighted matrix (confidence = alpha × event weight);
BPR learns to put a product the customer touched above a random one they did not touch.
A customer with no events before the period has no vector: they get the trending list.
"""

import os

import numpy as np

from . import Method, fill, top_k
from .popular import popular_list


def _threads():
    return int(os.environ.get("LARKFIELD_THREADS", "1"))


class Factorisation(Method):
    def fit(self):
        from implicit.als import AlternatingLeastSquares
        from implicit.bpr import BayesianPersonalizedRanking
        s = self.settings
        m = self.period.matrix()
        if s["algo"] == "als":
            self.model = AlternatingLeastSquares(factors=s.get("factors", 64), regularization=s.get("regularization", 0.05),
                                                 iterations=s.get("iterations", 15), alpha=s.get("alpha", 2.0),
                                                 random_state=s.get("seed", 37), num_threads=_threads())
        else:
            self.model = BayesianPersonalizedRanking(factors=s.get("factors", 64),
                                                     learning_rate=s.get("learning_rate", 0.05),
                                                     regularization=s.get("regularization", 0.01),
                                                     iterations=s.get("iterations", 100),
                                                     random_state=s.get("seed", 37), num_threads=_threads())
        self.model.fit(m, show_progress=False)
        self.user_factors = np.asarray(self.model.user_factors)
        self.item_factors = np.asarray(self.model.item_factors)
        self.known = np.asarray(m.sum(axis=1)).ravel() > 0
        self.fallback = popular_list(self.period, days=28)
        return self

    def scores(self, users):
        s = self.user_factors[users] @ self.item_factors.T
        s[~self.known[users]] = -np.inf
        return s

    def recommend(self, users, k=10):
        return fill(top_k(self.scores(users), k, self.period.available), self.fallback)


METHODS = {
    "als": (Factorisation, {"algo": "als"}, "matrix factorisation, alternating least squares (implicit)"),
    "bpr": (Factorisation, {"algo": "bpr"}, "matrix factorisation, Bayesian personalised ranking (implicit)"),
}
