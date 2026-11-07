import json

from detect import ledger


def _a(i, day="2025-10-06"):
    return {"alert_id": f"id-{i}", "day": day, "group": "customer", "key": f"C-{i}", "customers": [f"C-{i}"],
            "payments": [], "score": 1.0, "reasons": []}


def test_a_rerun_sends_nothing_twice(tmp_path):
    s, a = tmp_path / "state", tmp_path / "alerts"
    new, old = ledger.send([_a(1), _a(2)], "2025-10-06", s, a)
    assert (len(new), old) == (2, 0)
    new, old = ledger.send([_a(1), _a(2), _a(3)], "2025-10-06", s, a)
    assert (len(new), old) == (1, 2)
    lines = (a / "2025-10-06.jsonl").read_text().splitlines()
    assert [json.loads(x)["alert_id"] for x in lines] == ["id-1", "id-2", "id-3"]


def test_a_stop_between_the_two_writes_sends_nothing_twice(tmp_path):
    """The alert file was written, then the job stopped before the ledger: the next run must not resend."""
    s, a = tmp_path / "state", tmp_path / "alerts"
    ledger.send([_a(1)], "2025-10-06", s, a)
    (s / "sent.jsonl").unlink()
    new, old = ledger.send([_a(1)], "2025-10-06", s, a)
    assert (len(new), old) == (0, 1)
