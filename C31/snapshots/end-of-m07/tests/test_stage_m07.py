"""Service levels: the counter series start at 0, the stops are counted, and the week has sampled reviews."""

from pathlib import Path

from obs.alerts import indicators
from obs.model import Telemetry, load_events

DATA = Path(__file__).resolve().parent.parent / "data" / "telemetry"


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
