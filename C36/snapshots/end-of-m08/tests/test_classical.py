from larkroute.data import ROUTES
from larkroute.methods.classical import StrongRulesThenModel, TfidfNaiveBayes, TfidfSVM


def test_each_classical_model_trains_and_predicts_known_routes(small_train, tiny):
    for make in (TfidfNaiveBayes, TfidfSVM, StrongRulesThenModel):
        m = make().fit(small_train)
        pred = m.predict(tiny)
        assert len(pred) == len(tiny) and set(pred) <= set(ROUTES)
        p = m.proba(tiny)
        assert abs(p.sum(axis=1) - 1).max() < 1e-6


def test_a_strong_rule_wins_over_the_model(small_train, tiny):
    m = StrongRulesThenModel().fit(small_train)
    assert m.predict(tiny)[3] == "needs_person"  # "smoking": a safety rule
