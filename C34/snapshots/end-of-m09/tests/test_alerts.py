from detect import alerts
from detect import model as model_mod
from detect.score import score_day


def _alerts(payments, day):
    m = model_mod.train(payments, "2025-10-05", 60, history_days=10)
    return alerts.group(score_day(payments, day, m), m, day), m


def test_one_alert_for_the_stolen_card_with_reasons(payments):
    found, m = _alerts(payments, "2025-10-06")
    top = found[0]
    assert top["group"] == "customer" and top["key"] == "C-00007"
    assert len(top["payments"]) == 8
    feats = {r["feature"] for r in top["reasons"]}
    assert feats & {"new_device", "new_country", "payments_last_hour", "night"}
    assert top["runbook"]


def test_card_testing_is_one_device_alert(payments):
    found, m = _alerts(payments, "2025-10-07")
    dev = [a for a in found if a["group"] == "device"]
    assert len(dev) == 1 and dev[0]["key"] == "D-test0001" and len(dev[0]["customers"]) == 5


def test_budget_keeps_the_most_unusual(payments):
    found, m = _alerts(payments, "2025-10-06")
    kept = alerts.choose(found, "budget", 3, m.fixed_threshold)
    assert len(kept) == 3 and kept == found[:3]
    assert all(a["score"] >= m.fixed_threshold for a in alerts.choose(found, "fixed", 3, m.fixed_threshold))


def test_alert_id_does_not_depend_on_the_model():
    assert alerts.alert_id("2025-10-06", "customer", "C-00007") == alerts.alert_id("2025-10-06", "customer", "C-00007")
    assert alerts.alert_id("2025-10-06", "customer", "C-00007") != alerts.alert_id("2025-10-07", "customer", "C-00007")
