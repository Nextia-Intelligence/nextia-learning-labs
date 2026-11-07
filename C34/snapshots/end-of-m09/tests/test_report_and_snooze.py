import pytest

from detect import ledger, report, suppress


def _a(i, day, cust):
    return {"alert_id": f"id-{i}", "day": day, "group": "customer", "key": cust, "customers": [cust], "payments": [],
            "score": 1.0, "reasons": [{"feature": "new_device", "deviation": 9.0, "text": "a new device"}]}


def test_review_snooze_and_report(tmp_path):
    s, a = tmp_path / "state", tmp_path / "alerts"
    ledger.send([_a(1, "2025-10-06", "C-1"), _a(2, "2025-10-06", "C-2")], "2025-10-06", s, a)
    suppress.add_review(s, a, "id-1", "not")
    suppress.add_review(s, a, "id-2", "real")
    snoozed = suppress.snoozed_customers(s, "2025-10-08", 7)
    assert snoozed == {"C-1"}
    keep, held = suppress.apply([_a(3, "2025-10-08", "C-1"), _a(4, "2025-10-08", "C-3")], snoozed)
    assert [x["key"] for x in keep] == ["C-3"] and [x["key"] for x in held] == ["C-1"]
    assert suppress.snoozed_customers(s, "2025-10-20", 7) == set()
    text = report.weekly(s, a, "2025-10-12")
    assert "Precision of the reviewed alerts: 0.50 (1 of 2)" in text
    assert "new_device 2" in text


def test_review_of_an_unknown_alert_is_an_error(tmp_path):
    (tmp_path / "alerts").mkdir()
    with pytest.raises(SystemExit, match="No alert"):
        suppress.add_review(tmp_path, tmp_path / "alerts", "nope", "real")
    assert not (tmp_path / "reviews.jsonl").exists()
