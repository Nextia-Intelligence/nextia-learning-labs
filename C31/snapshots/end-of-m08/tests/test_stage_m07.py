"""Service levels: the counter series start at 0, the stops are counted, a ratio waits for enough runs, and a
person's review is attached to the run's trace."""

import json
from pathlib import Path

from obs.alerts import approvals, indicators, load_rules, review_table, reviews_of, timeline
from obs.model import Telemetry, load_events

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "telemetry"


def test_every_alert_series_starts_at_zero(telemetry_files):
    telemetry_files.flush()
    text = (telemetry_files.folder / "metrics.jsonl").read_text()
    assert '"name":"larkfield.writes"' in text and '"name":"larkfield.reconciles"' in text
    assert '"name":"larkfield.run.stops"' in text


def test_the_week_has_sampled_reviews():
    reviews = [e for e in load_events(DATA / "week") if e["name"] == "gen_ai.evaluation.result"]
    assert 40 <= len(reviews) <= 90 and all(e["trace_id"] for e in reviews)


def test_the_indicators_of_the_healthy_week():
    x = indicators(list(Telemetry(DATA / "healthy-week").runs.values()))
    assert x["unreconciled_writes"] == 0 and x["reply_failures"] == 0 and x["cost_per_resolved"] < 0.002


def test_the_help_desks_clock_stops_at_night():
    week = {a["run_id"]: a for a in approvals(list(Telemetry(DATA / "week").runs.values()))}
    hook = week["R-1014-040"]           # proposed Wed 17:52, decided Thu 09:17: 15 h 25 min, 47 min of it staffed
    assert 15 * 3600 < hook["wait_s"] < 16 * 3600 and 40 * 60 < hook["staffed_s"] < 50 * 60
    assert len(week) == 118 and all(a["staffed_s"] <= a["wait_s"] + 1 for a in week.values())


def test_a_ratio_alert_waits_for_enough_runs():
    rules = load_rules(PROJECT / "grafana" / "alerts" / "rules.json")
    handoff = [r for r in rules if r["uid"] == "handoff-rate"]
    healthy = list(Telemetry(DATA / "healthy-week").runs.values())
    # without the guard, 2 runs make a rate: the handoff alert fires on Monday morning of a healthy week
    noisy = timeline(healthy, handoff, min_runs=1)["handoff-rate"]
    assert noisy and noisy[0]["from_run"] < 20 and noisy[0]["runs"] < 20
    # with the rules file's guard, the healthy week is quiet and the real rise still fires (Saturday, run 282)
    assert not timeline(healthy, handoff)["handoff-rate"]
    fired = timeline(list(Telemetry(DATA / "week").runs.values()), handoff)["handoff-rate"]
    assert [p["from_run"] for p in fired] == [282] and len(fired[0]["examples"]) == 3
    # Grafana's ratio rules carry the same guard; a count of things that must not happen carries none
    text = (PROJECT / "grafana" / "alerts" / "agent-alerts.yaml").read_text()
    for rule in rules:
        block = text.split(f'uid: "{rule["uid"]}"')[1].split("- uid:")[0]
        guarded = f"and sum(increase(larkfield_runs_total[90s])) >= {rule.get('min_runs')}" in block
        assert guarded == (rule["indicator"] in ("handoff_rate", "cost_per_resolved")), rule["uid"]
        assert ("min_runs" in rule) == guarded, rule["uid"]   # obs: the same rules wait for 20 runs, the counts do not
        assert "example_runs:" in block and json.dumps(rule["example_query"])[1:-1] in block


def test_a_review_is_attached_to_the_runs_trace(telemetry_files, capsys):
    from resolver.__main__ import main
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    run_id = next(x for x in capsys.readouterr().out.split() if x.startswith("T-80008-"))
    main(["review", run_id, "fail", "--by", "usr-priya"])
    assert "fail, by usr-priya. Attached to trace" in capsys.readouterr().out
    telemetry_files.flush()
    t = Telemetry(telemetry_files.folder)
    review = reviews_of(t)[run_id]
    assert review["trace_id"] in t.runs[run_id].trace_ids
    assert review["attrs"]["gen_ai.evaluation.score.label"] == "fail"
    # the week's table: the German slice has 6 runs and one review
    rows = review_table(Telemetry(DATA / "week"), lambda r: r.language)
    assert rows[1].split()[:3] == ["de", "6", "1"] and rows[-1].startswith("Fewer than 5 reviews in: de, fr")
