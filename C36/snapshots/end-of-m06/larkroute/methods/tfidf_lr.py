"""TF-IDF features and logistic regression: the course's first trained model."""

from larkroute import tfidf
from larkroute.methods import Method, as_proba


class TfidfLogistic(Method):
    name = "TF-IDF + logistic regression"
    trains = True

    def fit(self, train):
        self.model = tfidf.logistic_regression().fit(train["text"], train["route"])
        return self

    def proba(self, messages):
        return as_proba(self.model.predict_proba(messages["text"]), self.model.classes_).set_index(messages.index)


METHODS = {TfidfLogistic.name: TfidfLogistic}
