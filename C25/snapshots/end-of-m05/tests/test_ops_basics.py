"""The ops tool's first commands (the MLOps course, Module 1), on a tiny telemetry file made
for the test (constructed: every number is visible here)."""

import json

from ops import files
from ops.__main__ import main
from ops.cmd_slo import evaluate
from ops.telemetry import Telemetry, percentile
from scripts import practice


def write(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


def received(t, tid, status=202):
    return {
        "signal": "log",
        "time": t,
        "event": "ticket.received",
        "attributes": {"ticket.id": tid, "http.status_code": status},
    }


def triaged(t, tid, outcome="ok", wait=30.0, team="delivery", needs=False, cost=0.0004):
    return {
        "signal": "log",
        "time": t + wait,
        "event": "ticket.triaged",
        "attributes": {
            "ticket.id": tid,
            "outcome": outcome,
            "time_to_draft_s": wait,
            "team": team,
            "needs_human": needs,
            "cost_usd": cost,
            "prompt.version": "assistant-v2",
            "evidence": "replayed",
        },
    }


def reviewed(t, tid, team="delivery", needs=False):
    return {
        "signal": "log",
        "time": t,
        "event": "ticket.reviewed",
        "attributes": {"ticket.id": tid, "label.team": team, "label.needs_human": needs},
    }


def week(tmp_path):
    """10 requests: 1 refused (503), 1 the caller's mistake (422), 8 accepted. Of the 8: one
    answer without text, one too late (700 s), 6 good. Reviews: 4 tickets, one wrong team, one
    safety ticket that the assistant did not send to a person."""
    r = [received(i * 10, f"T-{i}") for i in range(8)]
    r += [received(80, "T-8", 503), received(90, "T-9", 422)]
    r += [triaged(i * 10, f"T-{i}") for i in range(5)]
    r += [triaged(50, "T-5", outcome="no_answer"), triaged(60, "T-6", wait=700)]
    r += [triaged(70, "T-7", needs=False)]
    r += [
        reviewed(2000, "T-0"),
        reviewed(2000, "T-1", team="returns"),
        reviewed(2000, "T-2"),
        reviewed(2000, "T-7", needs=True),
    ]
    return write(tmp_path / "week.jsonl", r)


def test_the_slis_and_the_error_budgets(tmp_path):
    result = evaluate(Telemetry.load(week(tmp_path)), files.load("slos.toml"))
    rows = {r["id"]: r for r in result["rows"]}
    assert (rows["accept"]["good"], rows["accept"]["total"]) == (8, 9)  # the 422 is not counted
    assert (rows["draft"]["good"], rows["draft"]["total"]) == (6, 8)
    assert round(rows["draft"]["allowed"], 2) == 0.08  # 1% of 8 tickets
    assert round(rows["draft"]["burn"], 1) == 25.0  # 25% bad where 1% is allowed
    assert (rows["quality"]["good"], rows["quality"]["total"]) == (2, 4)
    assert (rows["safety"]["good"], rows["safety"]["total"]) == (0, 1)
    assert rows["safety"]["used"] == float("inf")  # no budget at all
    assert round(result["cost_per_1000"], 2) == 0.4


def test_last_n_tickets_and_the_command(tmp_path, capsys):
    path = week(tmp_path)
    result = evaluate(Telemetry.load(path), files.load("slos.toml"), last=2)
    assert result["tickets"] == 2
    assert main(["slo", str(path)]) == 0
    out = capsys.readouterr().out
    assert "draft" in out and "75.00% (6/8)" in out and "Grace" in out


def test_the_summary(tmp_path, capsys):
    assert main(["summary", str(week(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert "Ticket requests: 10 (202: 8, 422: 1, 503: 1)" in out
    assert "no_answer: 1" in out and "replayed 8 (100.00%)" in out


def test_the_inventory_has_an_owner_for_every_component(capsys):
    parts = files.load("inventory.toml")["component"]
    assert len(parts) >= 12 and all(c["owner"] and c["first_sign"] for c in parts)
    kinds = {c["kind"] for c in parts}
    assert {"code", "data", "model", "prompt", "index", "tool", "provider"} <= kinds
    assert main(["inventory", "--owner", "Priya"]) == 0
    assert "triage prompt" in capsys.readouterr().out


def test_nearest_rank_percentile():
    assert percentile([5, 1, 4, 2, 3], 50) == 3
    assert percentile([5, 1, 4, 2, 3], 95) == 5
    assert percentile([], 50) is None


def test_practice_tickets_are_the_evaluation_courses_tickets():
    tickets = practice.load_tickets()
    assert len(tickets) == 268  # 271 minus the 3 empty messages
    assert practice.subject_of("My parcel is late. It was due Monday.") == "My parcel is late"
    import random

    rng = random.Random(1)
    french = practice.choose(tickets, 2000, rng, {"lang:fr": 5.0})
    share = sum(t["language"] == "fr" for t in french) / 2000
    assert 0.25 < share < 0.40  # 21 of 268 tickets are French; 5 times more likely here
