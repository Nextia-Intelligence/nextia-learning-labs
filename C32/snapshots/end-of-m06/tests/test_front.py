"""The front door: one address, several replicas; what it sends again and what it does not."""

import httpx
from starlette.testclient import TestClient

from gateway.front import create_app


def replica(name):
    def handler(request: httpx.Request):
        if request.url.host == "dead":
            raise httpx.ConnectError("refused")
        if request.url.host == "dying":
            raise httpx.ReadError("connection reset")
        return httpx.Response(200, json={"replica": name, "path": request.url.path})
    return handler


def make(hosts):
    def handler(request):
        return replica(request.url.host)(request)
    app = create_app({h: f"http://{h}" for h in hosts}, transport=httpx.MockTransport(handler), check_seconds=3600)
    return app


def test_requests_go_round_the_healthy_replicas():
    app = make(["a", "b"])
    with TestClient(app) as c:
        got = [c.post("/v1/chat/completions", json={}).json()["replica"] for _ in range(4)]
    assert sorted(got) == ["a", "a", "b", "b"]


def test_a_refused_connection_is_sent_to_the_next_replica():
    app = make(["dead", "b"])
    with TestClient(app) as c:
        app.state.front.healthy["dead"] = True
        r = c.post("/v1/chat/completions", json={})
        assert r.status_code == 200 and r.headers["x-front-replica"] == "b"
        assert app.state.front.stats["retried_connect"] <= 1


def test_a_replica_that_dies_during_a_request_is_not_sent_it_again():
    app = make(["dying"])
    with TestClient(app) as c:
        app.state.front.healthy["dying"] = True
        r = c.post("/v1/chat/completions", json={})
    assert r.status_code == 502 and r.json()["error"]["code"] == "replica_failed"


def test_no_healthy_replica_is_a_clear_answer():
    app = make(["dead"])
    with TestClient(app) as c:
        app.state.front.healthy["dead"] = False
        r = c.post("/v1/chat/completions", json={})
    assert r.status_code == 503 and r.json()["error"]["code"] == "no_replica"
