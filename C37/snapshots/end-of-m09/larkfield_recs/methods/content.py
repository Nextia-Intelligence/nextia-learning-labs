"""Content-based suggestions: products whose text is close to the text of the customer's products.

Every product has an embedding of its title, description, category, style and colour (labs data
embeddings/products.npy, made once by the course with a small multilingual model). A new product has an
embedding on its first day, so content works with no interaction history.
"""

import numpy as np

from ..paths import data_dir
from . import Method, fill, top_k
from .neighbours import history_matrix
from .popular import popular_list


def embeddings():
    return np.load(data_dir() / "embeddings" / "products.npy").astype(np.float32)


class Content(Method):
    """Score = cosine between the product and the customer's profile (the weighted mean of their products)."""

    def fit(self):
        self.emb = embeddings()
        self.hist = history_matrix(self.period, self.settings.get("half_life", 30))
        self.fallback = popular_list(self.period, days=28)
        return self

    def profiles(self, users):
        prof = np.asarray(self.hist[users] @ self.emb)
        norm = np.linalg.norm(prof, axis=1, keepdims=True)
        norm[norm == 0] = 1
        return prof / norm

    def scores(self, users):
        s = self.profiles(users) @ self.emb.T
        s[np.asarray(self.hist[users].sum(axis=1)).ravel() == 0] = -np.inf
        return s

    def recommend(self, users, k=10):
        return fill(top_k(self.scores(users), k, self.period.available), self.fallback)

    def similar(self, product, n=10):
        s = self.emb @ self.emb[product]
        s[product] = -np.inf
        s[~self.period.available] = -np.inf
        order = np.argsort(-s)[:n]
        return order, s[order]


METHODS = {
    "content": (Content, {}, "content-based: products with text close to the customer's products (embeddings)"),
}
