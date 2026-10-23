"""The obs command line on the saved week (the outputs the lessons quote)."""

from pathlib import Path

from obs.__main__ import main

WEEK = ["--data", "data/telemetry/week"]
PROJECT = Path(__file__).resolve().parent.parent


def run(capsys, monkeypatch, *args):
    monkeypatch.chdir(PROJECT)
    main(list(args))
    return capsys.readouterr().out


def test_runs_lists_the_week(capsys, monkeypatch):
    out = run(capsys, monkeypatch, "runs", *WEEK, "--day", "wed", "--limit", "5")
    assert "R-1014-" in out and "run(s)" in out


def test_trace_shows_the_wait_and_the_two_refunds(capsys, monkeypatch):
    out = run(capsys, monkeypatch, "trace", "R-1014-040", *WEEK)
    assert "waited" in out and "for a person" in out and out.count("execute_tool request_refund") == 2
    assert "Flag duplicate_write" in out


def test_the_saved_trail_verifies(capsys, monkeypatch):
    assert "intact" in run(capsys, monkeypatch, "audit", "verify", *WEEK)


def test_events_of_one_run(capsys, monkeypatch):
    out = run(capsys, monkeypatch, "events", "R-1014-040", *WEEK)
    assert "larkfield.run.closed" in out


def test_find_counts_the_patterns(capsys, monkeypatch):
    out = run(capsys, monkeypatch, "find", "loop", *WEEK)
    assert "match(es) in 316 run(s)" in out
    out = run(capsys, monkeypatch, "runs", *WEEK, "--flag", "duplicate_write")
    assert "R-1014-040" in out
    # the metric around the no-action runs: 9 failed replies on Thursday, each point with an example trace
    out = run(capsys, monkeypatch, "metrics", "larkfield.tool.calls", "--where", "gen_ai.tool.name=send_reply",
              "--where", "larkfield.tool.status=failed", *WEEK)
    assert "R-1015-017 (trace f62fe6a2)" in out and "4 interval(s) with an increase, 4 with an example trace" in out


def test_cost_by_model_the_budget_and_the_gateways_split(capsys, monkeypatch):
    out = run(capsys, monkeypatch, "cost", "--by", "model", *WEEK)
    assert "chat-strong" in out and "per resolved" in out
    # the budget window goes over US$0.002 when the alert rule does (Wed 10:39, closed run 120) and names its runs
    out = run(capsys, monkeypatch, "cost", "--budget", "0.002", *WEEK)
    assert "Over budget at Wed 14 Oct 10:39 (closed run 120" in out and "chat-strong" in out
    assert "Never over budget." in run(capsys, monkeypatch, "cost", "--budget", "0.002", "--data", "data/telemetry/healthy-week")
    usage = "data/telemetry/gateway/gateway-usage.json"
    out = run(capsys, monkeypatch, "gateway", usage, "--by", "team")
    assert "service" in out and "0.77710" in out


