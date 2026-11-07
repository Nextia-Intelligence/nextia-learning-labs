from larkroute import tfidf
from larkroute.commands.explain import top_features


def test_the_top_features_come_from_the_message(small_train):
    model = tfidf.logistic_regression().fit(small_train["text"], small_train["route"])
    feats = top_features(model, "I was charged twice on my card", "billing", n=5)
    assert len(feats) == 5
    assert any("charg" in f for f, _ in feats)
