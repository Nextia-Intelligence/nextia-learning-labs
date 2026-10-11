"""Monitoring changing behaviour (the MLOps course, Module 4): drift statistics, agents' reviews
(delayed labels), the answers' retrieval index and old sources."""

import json
from collections import Counter

from test_jobs import TICKET, run_worker

from ops import stats
from ops.__main__ import main
from scripts import reindex, update_document


def test_psi_and_chi_square_on_a_tiny_example():
    same = Counter({"en": 90, "fr": 10})
    assert stats.psi(same, same) == 0
    moved = Counter({"en": 60, "fr": 40})
    # (0.6-0.9) ln(0.6/0.9) + (0.4-0.1) ln(0.4/0.1) = 0.1216 + 0.4159
    assert round(stats.psi(same, moved), 4) == 0.5375
    chi, df, p = stats.chi_square(Counter({"a": 50, "b": 50}), Counter({"a": 30, "b": 70}))
    assert (round(chi, 3), df, round(p, 5)) == (8.333, 1, 0.00389)
    assert stats.chi_square(same, same)[2] == 1.0


def test_wilson_interval_and_reviews_needed():
    lo, hi = stats.wilson(45, 50)
    assert (round(lo, 3), round(hi, 3)) == (0.786, 0.957)
    assert stats.reviews_needed(0.9, 0.05) == 139


def telemetry_file(tmp_path, french_before=0.1, french_after=0.4, n=400):
    rows = []
    for i in range(n):
        share = french_before if i < n // 2 else french_after
        lang = "fr" if (i % 100) < share * 100 else "en"
        t = i * 6.0
        rows.append(
            {
                "signal": "log",
                "time": t,
                "event": "ticket.received",
                "attributes": {
                    "ticket.id": f"T-{i}",
                    "http.status_code": 202,
                    "ticket.language_guess": lang,
                    "ticket.message_chars": 200 + i % 50,
                    "ticket.channel": "web_form",
                },
            }
        )
        rows.append(
            {
                "signal": "log",
                "time": t + 3,
                "event": "ticket.triaged",
                "attributes": {
                    "ticket.id": f"T-{i}",
                    "outcome": "ok",
                    "team": "delivery",
                    "needs_human": False,
                    "prompt.version": "assistant-v2",
                    "gen_ai.response.model": "gpt-6-luna-2026-09-22",
                },
            }
        )
        if i % 2 == 0:
            right = "returns" if lang == "fr" and i >= n // 2 else "delivery"
            rows.append(
                {
                    "signal": "log",
                    "time": t + 600,
                    "event": "ticket.reviewed",
                    "attributes": {
                        "ticket.id": f"T-{i}",
                        "label.team": right,
                        "label.needs_human": False,
                        "review.delay_s": 597,
                    },
                }
            )
    path = tmp_path / "t.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_drift_finds_more_french_tickets(tmp_path, capsys):
    path = telemetry_file(tmp_path)
    assert main(["drift", str(path), "--at", "20"]) == 0  # 200 tickets x 6 s = 20 minutes
    out = capsys.readouterr().out
    line = next(x for x in out.splitlines() if "language_guess" in x)
    assert "LARGE change" in line and "fr 10% -> 40%" in line
    team = next(x for x in out.splitlines() if " team " in f" {x} ")
    assert "no real change" in team  # the assistant still says delivery for all
    assert main(["drift", str(path), "--windows", "100"]) == 0


def test_labels_show_the_drop_that_drift_cannot(tmp_path, capsys):
    assert main(["labels", str(telemetry_file(tmp_path)), "--windows", "200"]) == 0
    out = capsys.readouterr().out
    rows = [x for x in out.splitlines() if x.strip().startswith(("1-", "201-"))]
    assert "100.0%" in rows[0] and "60.0%" in rows[1]  # 40 of 100 reviews disagree after


def test_an_agents_review_is_compared_with_the_decision(api, db_url, conn):
    r = api.post("/v1/tickets", json=TICKET).json()
    run_worker(db_url)
    review = api.post(
        f"/v1/tickets/{r['ticket_id']}/review",
        json={"team": "payment", "needs_human": False, "reviewed_by": "agent-07"},
    )
    assert review.status_code == 200, review.text
    body = review.json()
    assert body["agrees"] is True and body["assistant_team"] == "payment"
    assert body["prompt_version"] == "assistant-v2" and body["delay_seconds"] >= 0
    wrong = api.post(
        f"/v1/tickets/{r['ticket_id']}/review",
        json={"team": "returns", "needs_human": True, "reviewed_by": "agent-02"},
    )
    assert wrong.json()["agrees"] is False  # a second review replaces the first
    assert conn.execute("SELECT count(*) AS n FROM ticket_reviews").fetchone()["n"] == 1
    missing = api.post(
        "/v1/tickets/T-999999/review",
        json={"team": "returns", "needs_human": True, "reviewed_by": "agent-02"},
    )
    assert missing.status_code == 404


def test_a_document_changes_and_the_index_is_stale_until_rebuilt(api, monkeypatch, db_url, capsys):
    monkeypatch.setenv("DATABASE_URL", db_url)
    q = {"question": "Where is my parcel and how do I track it?"}
    h = {"X-Customer-ID": "C-0003"}
    first = api.post("/v1/answers", json=q, headers=h).json()
    assert "delivery-policy" in first["sources"] and first["stale_sources"] == 0
    assert update_document.main(["delivery-policy", "--replace", "free at 100", "free at 75"]) == 0
    second = api.post("/v1/answers", json=q, headers=h).json()
    assert second["stale_sources"] == 1  # the index still has the old version
    assert reindex.main(["--check"]) == 1
    assert reindex.main([]) == 0
    third = api.post("/v1/answers", json=q, headers=h).json()
    assert third["stale_sources"] == 0
    assert "delivery-policy@4" in first["source_versions"]
    assert "delivery-policy@5" in third["source_versions"]


def test_rag_report(tmp_path, capsys):
    rows = [
        {
            "signal": "log",
            "time": 0,
            "event": "answer.served",
            "attributes": {
                "sources": ["delivery-policy@4"],
                "stale_sources": 0,
                "index.version": "a",
                "docs.version": "a",
            },
        },
        {
            "signal": "log",
            "time": 400,
            "event": "answer.served",
            "attributes": {
                "sources": ["delivery-policy@4"],
                "stale_sources": 1,
                "index.version": "a",
                "docs.version": "b",
            },
        },
        {
            "signal": "log",
            "time": 420,
            "event": "ticket.triaged",
            "attributes": {"ticket.id": "T-1", "gen_ai.response.model": "gpt-6-luna-2026-11-01"},
        },
    ]
    path = tmp_path / "t.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert main(["rag", str(path)]) == 0
    out = capsys.readouterr().out
    assert "1 (100%)" in out and "gpt-6-luna-2026-11-01 1" in out
