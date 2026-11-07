"""Naive Bayes and a linear SVM on TF-IDF features, and rules that work with the model."""

from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from larkroute import rules as rule_book
from larkroute import tfidf
from larkroute.methods import Method, as_proba
from larkroute.methods.tfidf_lr import TfidfLogistic


class _Pipeline(Method):
    trains = True

    def proba(self, messages):
        return as_proba(self.model.predict_proba(messages["text"]), self.model.classes_).set_index(messages.index)


class TfidfNaiveBayes(_Pipeline):
    name = "TF-IDF + Naive Bayes"

    def fit(self, train):
        nb = make_pipeline(tfidf.features(chars=False), ComplementNB(alpha=0.3))
        self.model = nb.fit(train["text"], train["route"])
        return self


class TfidfSVM(_Pipeline):
    name = "TF-IDF + linear SVM"

    def fit(self, train):
        # The SVM gives scores, not probabilities: the calibration step turns them into probabilities.
        svm = CalibratedClassifierCV(LinearSVC(C=0.5), cv=3)
        self.model = make_pipeline(tfidf.features(), svm).fit(train["text"], train["route"])
        return self


class StrongRulesThenModel(TfidfLogistic):
    """Strong rules decide first (the cases Grace trusts more than a model); the model decides the rest."""
    name = "strong rules + logistic regression"

    def fit(self, train):
        self.rules = rule_book.load()
        return super().fit(train)

    def predict(self, messages):
        model = super().predict(messages)
        out = []
        for text, m in zip(messages["text"], model, strict=True):
            r = rule_book.match(text, self.rules, strong_only=True)
            out.append(r["route"] if r else m)
        return out


METHODS = {c.name: c for c in (TfidfNaiveBayes, TfidfSVM, StrongRulesThenModel)}
