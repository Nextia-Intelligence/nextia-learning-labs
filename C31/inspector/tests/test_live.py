"""Live mode with test answers in the shapes of Tempo's and Prometheus's HTTP APIs (not a real Tempo)."""

import json
import urllib.parse

import pytest
from conftest import FIXTURES

from larkfield_inspector.server import Inspector
from larkfield_inspector.sources import LiveSource, hex_id, spans_from_otlp


class FakeHttp:
    def __init__(self, fail=False):
        self.urls = []
        self.fail = fail

    def __call__(self, url, timeout=10.0):
        self.urls.append(url)
        if self.fail:
            raise ConnectionRefusedError("connection refused")
        parsed = urllib.parse.urlparse(url)
        if parsed.path == "/api/search":
            return json.loads((FIXTURES / "tempo_search.json").read_text())
        if parsed.path.startswith("/api/traces/"):
            return json.loads((FIXTURES / f"tempo_trace_{parsed.path.rsplit('/', 1)[1]}.json").read_text())
        if parsed.path == "/api/v1/query_range":
            return json.loads((FIXTURES / "prometheus_query_range.json").read_text())
        raise AssertionError(url)


@pytest.fixture
def live(tmp_path):
    env = {"TEMPO_URL": "http://tempo.test:3200", "PROMETHEUS_URL": "http://prom.test:9090",
           "AUDIT_STORE": str(FIXTURES.parent.parent / "larkfield_inspector" / "data" / "week" / "audit.jsonl")}
    http = FakeHttp()
    src = LiveSource(env, get=http)
    src.now = lambda: 1792300000
    return Inspector("live", env=env, live=src), http


def test_ids():
    assert hex_id("8EM8RAPidn4daezhipR1Jg==", 16) == "f0433c4403e2767e1d69ece18a947526"
    assert hex_id("f0433c4403e2767e1d69ece18a947526", 16) == "f0433c4403e2767e1d69ece18a947526"
    assert hex_id("433c4403e2767e1d69ece18a947526", 16) == "00433c4403e2767e1d69ece18a947526"
    assert hex_id("eNJG7iLl9e8=", 8) == "78d246ee22e5f5ef"


def test_both_shapes():
    doc = json.loads((FIXTURES / "tempo_trace_f0433c4403e2767e1d69ece18a947526.json").read_text())
    spans = spans_from_otlp(doc)
    as_resource_spans = spans_from_otlp({"resourceSpans": doc["batches"]})
    as_v2 = spans_from_otlp({"trace": {"resourceSpans": doc["batches"]}})
    assert [s.span_id for s in spans] == [s.span_id for s in as_resource_spans] == [s.span_id for s in as_v2]
    assert all(len(s.trace_id) == 32 and len(s.span_id) == 16 for s in spans)
    assert {s.kind for s in spans} <= {"internal", "client"}


def test_live_runs_match_saved_mode(live, app):
    inspector, http = live
    runs = inspector.runs({})
    assert runs["dataset"] == "live" and runs["error"] == ""
    ids = {r["run_id"] for r in runs["runs"]}
    assert ids == {"R-1014-040", "R-1012-034", "R-1018-010"}
    for rid in ids:
        saved = app.sources["week"].runs[rid]
        got = next(r for r in runs["runs"] if r["run_id"] == rid)
        assert got["flags"] == sorted(saved.flags) and got["cost"] == saved.cost and got["outcome"] == saved.outcome
    d = inspector.run("R-1014-040", {})
    assert len(d["traces"]) == 2 and d["waits"][0]["approver"] == "usr-sam"
    assert {f["name"] for f in d["flags"]} == {"duplicate_write"}
    assert any("/api/search?" in u and "start=" in u and "end=" in u and "limit=" in u for u in http.urls)
    assert all(u.startswith(("http://tempo.test:3200/", "http://prom.test:9090/")) for u in http.urls)


def test_live_cost_and_audit(live):
    inspector, _ = live
    c = inspector.cost({})
    assert c["prometheus"]["available"] and c["prometheus"]["series"][0]["points"][0][1] == 0.0123
    a = inspector.audit("R-1014-040", {})
    assert a["verify"]["ok"]


def test_tempo_down(tmp_path):
    src = LiveSource({"TEMPO_URL": "http://127.0.0.1:9"}, get=FakeHttp(fail=True))
    inspector = Inspector("live", env={}, live=src)
    runs = inspector.runs({})
    assert runs["runs"] == [] and "connection refused" in runs["error"]
    assert inspector.cost({})["prometheus"]["available"] is False
    assert inspector.runs({"ds": "week"})["shown"] > 0   # the built-in data stays available
