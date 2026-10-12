"""Release gates and controlled rollouts (the MLOps course, Module 5)."""

import json

import pytest
from test_jobs import TICKET, run_worker
from test_releases import write_release

from ops.__main__ import main
from ticket_api import releases, rollout


def test_the_canary_share_is_stable_and_about_right():
    ids = [f"T-{500001 + i}" for i in range(5000)]
    state = rollout.State("v2", "v3", 0.1, None)
    picked = [rollout.choose(state, t) for t in ids]
    assert 0.08 < picked.count("v3") / len(ids) < 0.12
    assert picked == [rollout.choose(state, t) for t in ids]  # the same ticket, the same release
    assert rollout.choose(rollout.State("v2", None, 0.0, None), ids[0]) == "v2"


def test_the_gate_stops_prompt_v3_and_passes_prompt_v2(capsys):
    assert main(["gate", "assistant-v3"]) == 1
    out = capsys.readouterr().out
    assert "DO NOT SHIP" in out and "T-65663 no_answer_critical" in out
    assert main(["gate", "assistant-v2"]) == 0
    assert "SHIP to a canary" in capsys.readouterr().out


@pytest.fixture
def two_releases(tmp_path, monkeypatch, db_url):
    monkeypatch.setattr(releases, "FOLDER", tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    v2, v3 = write_release(tmp_path), write_release(tmp_path, "assistant-v3")
    return v2["id"], v3["id"]


def test_canary_rollback_and_history(two_releases, make_api, db_url, conn, capsys):
    v2, v3 = two_releases
    assert main(["rollout", "start", v2]) == 0
    assert main(["rollout", "canary", v3, "--share", "0.5", "--reason", "try v3"]) == 0
    api = make_api()
    tickets = [
        api.post("/v1/tickets", json={**TICKET, "body": f"Two payments, {i}."}).json()
        for i in range(12)
    ]
    run_worker(db_url)
    rows = conn.execute(
        "SELECT ticket_id, release_id, prompt_version FROM ai_runs WHERE task = 'triage'"
    ).fetchall()
    by_ticket = {r["ticket_id"]: r for r in rows}
    for t in tickets:
        expected = v3 if rollout.bucket(t["ticket_id"]) < 0.5 else v2
        assert by_ticket[t["ticket_id"]]["release_id"] == expected
        assert by_ticket[t["ticket_id"]]["prompt_version"] == (
            "assistant-v3" if expected == v3 else "assistant-v2"
        )
    assert main(["rollout", "rollback", "--reason", "answers without text"]) == 0
    assert main(["rollout", "status"]) == 0
    out = capsys.readouterr().out
    assert f"active {v2}" in out.splitlines()[-1] and "canary" not in out.splitlines()[-1]
    assert main(["rollout", "history"]) == 0
    assert "answers without text" in capsys.readouterr().out


def test_a_release_without_a_manifest_is_refused(two_releases):
    assert main(["rollout", "start", "1.5.0-000000"]) == 2


def test_a_shadow_release_runs_beside_and_changes_nothing(two_releases, make_api, db_url, conn):
    v2, v3 = two_releases
    main(["rollout", "start", v2])
    main(["rollout", "shadow", v3])
    t = make_api().post("/v1/tickets", json=TICKET).json()
    worker = run_worker(db_url)
    assert worker.counts["succeeded"] == 1
    runs = conn.execute(
        "SELECT task, release_id, status FROM ai_runs WHERE ticket_id = %s ORDER BY run_id",
        (t["ticket_id"],),
    ).fetchall()
    assert [(r["task"], r["release_id"]) for r in runs] == [
        ("triage", v2),
        ("embed", v2),
        ("triage_shadow", v3),
    ]


def write(tmp_path, rows):
    path = tmp_path / "t.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_canary_report_finds_the_first_answer_without_text(tmp_path, capsys):
    rows = []
    for i in range(200):
        canary = i % 10 == 0
        outcome = "no_answer" if canary and i == 70 else "ok"
        rows.append(
            {
                "signal": "log",
                "time": float(i),
                "event": "ticket.triaged",
                "attributes": {
                    "ticket.id": f"T-{i}",
                    "outcome": outcome,
                    "release.canary": canary,
                    "release.id": "v3" if canary else "v2",
                    "cost_usd": 0.0005 if canary else 0.0003,
                    "triage_ms": 6000 if canary else 3000,
                    "team": "delivery",
                    "needs_human": False,
                },
            }
        )
    rows.append(
        {
            "signal": "log",
            "time": 120.0,
            "event": "release.changed",
            "attributes": {"release.active": "v2", "release.canary": None},
        }
    )
    assert main(["canary", str(write(tmp_path, rows))]) == 0
    out = capsys.readouterr().out
    assert "no answer    at +1.2 min: after 8 canary tickets (71 tickets in all)" in out
    assert "cost" not in out.split("Rollback rules met")[1].split("After")[0]  # 20 < 50 tickets
    assert "After the last release change" in out
