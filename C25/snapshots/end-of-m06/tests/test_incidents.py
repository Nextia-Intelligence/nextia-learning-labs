"""Incidents (the MLOps course, Module 6): what customers see, the alert rules on saved
telemetry, the timeline and the recovery checks."""

import json

from ops import files
from ops.__main__ import main
from ops.cmd_alerts import evaluate
from ops.telemetry import Telemetry
from ticket_api.job_routes import status_message


def test_customers_see_a_clear_status():
    ok = status_message({"queued": 3, "oldest_queued_seconds": 4.0, "succeeded_last_minute": 60})
    assert ok.status == "ok"
    late = status_message(
        {"queued": 300, "oldest_queued_seconds": 400.0, "succeeded_last_minute": 60}
    )
    assert late.status == "delayed" and "about 5 minutes" in late.message
    assert "nothing is lost" in late.message and "send your ticket again" in late.message


def test_the_status_endpoint_needs_no_key(make_api):
    api = make_api(api_key="secret-key")
    r = api.get("/v1/status")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def outage_file(tmp_path):
    """Constructed: 1 ticket every 10 s for 20 minutes; the provider fails from minute 5 to 10,
    so tickets wait until minute 10 and are then drafted."""
    rows = [
        {
            "signal": "log",
            "time": 0.0,
            "event": "practice.action",
            "attributes": {"action": "scenario start"},
        }
    ]
    for i in range(120):
        t = i * 10.0
        done = 600.0 + (i - 30) * 2 if 300 <= t < 600 else t + 5
        rows.append(
            {
                "signal": "log",
                "time": t,
                "event": "ticket.received",
                "attributes": {"ticket.id": f"T-{i}", "http.status_code": 202},
            }
        )
        rows.append(
            {
                "signal": "log",
                "time": done,
                "event": "ticket.triaged",
                "attributes": {
                    "ticket.id": f"T-{i}",
                    "outcome": "ok",
                    "time_to_draft_s": done - t,
                    "cost_usd": 0.0003,
                    "triage_ms": 3000,
                },
            }
        )
    rows += [
        {
            "signal": "log",
            "time": 300.0,
            "event": "practice.action",
            "attributes": {"action": "simulator mode", "mode": "outage"},
        },
        {
            "signal": "log",
            "time": 310.0,
            "event": "breaker.changed",
            "attributes": {"breaker.state": "open"},
        },
        {
            "signal": "log",
            "time": 610.0,
            "event": "breaker.changed",
            "attributes": {"breaker.state": "closed"},
        },
    ]
    path = tmp_path / "outage.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_the_alerts_fire_and_resolve_on_saved_telemetry(tmp_path):
    fired = evaluate(Telemetry.load(outage_file(tmp_path)), files.load("alerts.toml")["alert"])
    assert fired["provider-circuit-open"] == [(340.0, 610.0)]  # open at 310, for 30 s
    start, end = fired["drafts-late"][0]
    assert start == 490.0  # the oldest ticket (300 s) is over 120 s at 430, then 60 s more
    assert fired["no-answer"] == [] and fired["accept-fast-burn"] == []


def test_the_incident_timeline_and_recovery(tmp_path, capsys):
    assert main(["incident", str(outage_file(tmp_path)), "--minute", "5"]) == 0
    out = capsys.readouterr().out
    assert "provider-circuit-open fired" in out and "circuit open" in out
    assert "[x] nothing is waiting long" in out
    assert main(["alerts", str(outage_file(tmp_path)), "--after", "simulator mode"]) == 0
    assert "0.7 min" in capsys.readouterr().out  # the circuit alert, 40 s after the outage
