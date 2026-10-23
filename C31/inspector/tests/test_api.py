"""The HTTP API, on a server started for the tests."""

import json

from conftest import get


def j(server, path):
    status, headers, body = get(server + path)
    assert status == 200, (path, body[:300])
    assert headers["Content-Type"].startswith("application/json")
    return json.loads(body)


def test_info(server):
    info = j(server, "/api/info")
    assert info["mode"] == "saved" and info["default"] == "week"
    assert [d["id"] for d in info["datasets"]] == ["week", "healthy-week", "constructed"]
    assert info["flags"] == ["loop", "hidden_tool_error", "duplicate_write", "no_action", "followed_injection"]
    assert info["budget_per_resolved"] == 0.002


def test_runs_and_filters(server):
    all_runs = j(server, "/api/runs")
    assert all_runs["shown"] == all_runs["total"] > 0
    flagged = j(server, "/api/runs?flag=any")
    assert flagged["shown"] == all_runs["flagged"] and all(r["flags"] for r in flagged["runs"])
    small = j(server, "/api/runs?model=chat-small&outcome=resolved&language=en")
    assert all(r["model"] == "chat-small" and r["outcome"] == "resolved" and r["language"] == "en" for r in small["runs"])
    cheap = j(server, "/api/runs?max_cost=0.0006&min_cost=0.0005")
    assert all(0.0005 <= r["cost"] <= 0.0006 for r in cheap["runs"])
    first = all_runs["runs"][0]["start"]
    window = j(server, f"/api/runs?from={first}&to={first + 3600_000}")
    assert window["shown"] >= 1 and all(first <= r["start"] < first + 3600_000 for r in window["runs"])
    ticket = j(server, "/api/runs?ticket=T-90104")
    assert {r["ticket"] for r in ticket["runs"]} == {"T-90104"}
    by_cost = j(server, "/api/runs?sort=cost&order=desc")["runs"]
    assert by_cost[0]["cost"] >= by_cost[-1]["cost"]


def test_one_run(server):
    d = j(server, "/api/runs/R-1014-040")
    assert d["run"]["ticket"] == "T-90104"
    assert len(d["traces"]) == 2
    assert d["waits"][0]["approver"] == "usr-sam" and d["waits"][0]["approver_name"] == "Sam"
    assert d["waits"][0]["seconds"] > 3600
    flag = {f["name"]: f for f in d["flags"]}["duplicate_write"]
    assert "written twice" in flag["why"] and len(flag["spans"]) == 2
    writes = [s for t in d["traces"] for s in t["spans"] if s["tool"] == "request_refund"]
    assert [s["error"] for s in writes] == [True, False] and writes[1]["retry"]
    assert "grafana" in d["traces"][0]["links"] and "langfuse" not in d["traces"][0]["links"]
    assert d["price_tables"] and "R-1012-034" in d["same_ticket"]
    model = [s for s in d["traces"][0]["spans"] if s["kind"] == "model"]
    assert all(s["tokens_in"] and s["cost"] for s in model)


def test_by_ticket_and_unknown_run(server):
    assert j(server, "/api/runs/T-90104")["run"]["ticket"] == "T-90104"
    status, _, body = get(server + "/api/runs/R-0000-000")
    assert status == 404 and "There is no run" in json.loads(body)["error"]
    status, _, _ = get(server + "/api/runs?ds=nothing")
    assert status == 404


def test_audit(server):
    a = j(server, "/api/runs/R-1014-040/audit")
    assert a["verify"]["ok"] and a["ticket"] == "T-90104"
    assert [r["type"] for r in a["records"]][:2] == ["data_access", "proposal"]
    assert all(r["links_ok"] for r in a["records"])
    change = a["changes"][0]
    assert change["calls"] == 2 and change["outcomes"] == ["timeout", "done"] and len(change["keys"]) == 2
    approval = next(r for r in a["records"] if r["type"] == "approval")
    assert approval["actor"]["name"] == "Sam"


def test_cost(server):
    c = j(server, "/api/cost")
    assert c["budget_per_resolved"] == 0.002 and c["price_tables"]
    assert c["total"]["runs"] == sum(b["runs"] for b in c["series"])
    assert len(c["top"]) == 10 and c["top"][0]["cost"] >= c["top"][-1]["cost"]
    assert {g["key"] for g in c["groups"]["model"]} >= {"chat-small", "chat-strong"}
    hours = j(server, "/api/cost?bucket=hour&model=chat-strong")
    assert hours["bucket"] == "hour" and len(hours["series"]) > len(c["series"])
    assert hours["total"]["runs"] == sum(1 for r in j(server, "/api/runs?model=chat-strong")["runs"])


def test_cost_rises_after_the_model_switch(server):
    c = j(server, "/api/cost")
    rel = {r["release"]: r["first_run"] for r in c["releases"]}
    switch = min(v for k, v in rel.items() if k != min(rel))
    before = [b for b in c["series"] if b["end"] <= switch and b["per_resolved"]]
    after = [b for b in c["series"] if b["start"] >= switch and b["per_resolved"]]
    assert max(b["per_resolved"] for b in before) < min(b["per_resolved"] for b in after)


def test_compare(server):
    c = j(server, "/api/compare?a=R-1014-040&b=R-1012-034")
    assert c["same_ticket"]
    fd = c["first_difference"]
    assert fd["kind"] == "model_decision"
    assert fd["a"]["value"]["proposal"] != fd["b"]["value"]["proposal"]
    assert any(r["a"] and r["a"]["sig"] == "approval" and r["b"] is None for r in c["rows"])
    default = j(server, "/api/compare")
    assert default["a"]["ticket"] == default["b"]["ticket"]
    same = j(server, "/api/compare?a=R-1014-040&b=R-1014-040")
    assert same["first_difference"] is None


def test_read_only_and_headers(server):
    status, headers, _ = get(server + "/api/runs", method="POST")
    assert status == 405
    status, headers, _ = get(server + "/api/info")
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_pages(server):
    status, headers, body = get(server + "/")
    assert status == 200 and headers["Content-Type"].startswith("text/html") and b'id="root"' in body
    status, _, body = get(server + "/../../../etc/passwd")
    assert status == 200 and b'id="root"' in body   # never a file outside the pages
    status, _, body = get(server + "/%2e%2e/sync.py")
    assert b"shutil" not in body
