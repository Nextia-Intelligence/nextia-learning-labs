from larkspeech import data as D
from larkspeech import understand as U


def test_rules_and_classifier(data):
    assert U.rule_reason("I was charged twice on my card") == "billing"
    assert U.rule_reason("je veux annuler ma commande", "fr") == "cancel_order"
    train = D.load_calls(data)
    clf = U.ReasonClassifier().fit([D.reference(c) for c in train], [c["reason"] for c in train])
    assert clf.predict(["charged twice on my card"]) == ["billing"]


def test_notice_exact_and_fuzzy():
    said = "Thank you for calling Larkfield. This call is recorded for quality and training."
    variant = "Just so you know, calls may be recorded for training and quality purposes."
    assert U.notice_exact(said, "en") and not U.notice_exact(variant, "en")
    assert U.notice_fuzzy(variant, "en") and not U.notice_fuzzy("How can I help you today?", "en")


def test_recorded_llm(data):
    assert U.load_llm(data, "reason-reference")["T-0003"]["answer"]["reason"] == "order_status"
