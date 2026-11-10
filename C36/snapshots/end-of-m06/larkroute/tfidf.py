"""Text as numbers: TF-IDF features of words and of character n-grams, in one scikit-learn pipeline."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, make_pipeline


def features(chars: bool = True) -> FeatureUnion | TfidfVectorizer:
    """Words and word pairs; with chars=True, also character n-grams of 2 to 5 letters (typos, French endings)."""
    words = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, strip_accents="unicode")
    if not chars:
        return words
    letters = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)
    return FeatureUnion([("words", words), ("chars", letters)])


def logistic_regression(chars: bool = True, class_weight=None):
    return make_pipeline(features(chars), LogisticRegression(C=10, max_iter=3000, class_weight=class_weight))
