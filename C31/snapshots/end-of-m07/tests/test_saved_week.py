"""The saved week: every scenario shows its flag, the healthy week shows none, and the alerts fire on time."""

import json
from pathlib import Path

import pytest

from obs.alerts import load_rules, timeline
from obs.model import Telemetry

DATA = Path(__file__).resolve().parent.parent / "data" / "telemetry"
EXPECT = {"double_refund": "duplicate_write", "loop": "loop", "no_action": "no_action",
          "hidden_tool_error": "hidden_tool_error"}


@pytest.fixture(scope="module")
def week():
    return Telemetry(DATA / "week")


@pytest.fixture(scope="module")
def healthy():
    return Telemetry(DATA / "healthy-week")


def test_every_scenario_run_has_its_flag(week):
    truth = json.loads((DATA / "week" / "truth.json").read_text())["runs"]
    assert len(truth) == len(week.runs) == 316
    for t in truth:
        for scenario, flag in EXPECT.items():
            if scenario in t["scenarios"]:
                assert flag in week.runs[t["run_id"]].flags, (t["run_id"], scenario)


def test_the_injected_instructions_were_not_followed(week):
    truth = json.loads((DATA / "week" / "truth.json").read_text())["runs"]
    seen = [t["run_id"] for t in truth if "injection_seen" in t["scenarios"]]
    assert seen and not any("followed_injection" in week.runs[r].flags for r in seen)


def test_the_constructed_run_followed_an_injection():
    run = Telemetry(DATA / "constructed").runs["C-1016-001"]
    assert "followed_injection" in run.flags


def test_the_healthy_week_has_no_flag(healthy):
    assert not any(r.flags for r in healthy.runs.values())


def test_the_healthy_week_has_no_alert(healthy):
    rules = load_rules(Path(__file__).resolve().parent.parent / "grafana" / "alerts" / "rules.json")
    assert all(not periods for periods in timeline(list(healthy.runs.values()), rules).values())


def test_every_alert_fires_on_the_week(week):
    rules = load_rules(Path(__file__).resolve().parent.parent / "grafana" / "alerts" / "rules.json")
    fired = timeline(list(week.runs.values()), rules)
    assert all(fired[r["uid"]] for r in rules)




def test_the_double_refund_run(week):
    run = week.runs["R-1014-040"]
    assert run.ticket == "T-90104" and len(run.trace_ids) == 2 and run.wait_s > 8 * 3600
    assert run.outcome == "resolved" and "duplicate_write" in run.flags


def test_the_saved_audit_trail_verifies():
    from auditstore.store import AuditStore
    assert AuditStore(DATA / "week" / "audit.jsonl").verify()["ok"]
