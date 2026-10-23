"""The apps' recorded request streams, and the replayer that sends them."""

import httpx
from starlette.testclient import TestClient

from apps.client import Sender
from apps.replay import APPS, pick, request_for, units


def test_every_app_has_its_recorded_stream():
    counts = {app: len(units(app)) for app in APPS}
    assert counts == {"ticket-triage": 679, "support-workflow": 210, "doc-assistant": 353, "release-judge": 400}


def test_a_triage_unit_is_one_chat_call_and_one_embedding():
    u = next(u for u in units("ticket-triage") if u.group == "T-64701")
    assert [r["endpoint"] for r in u.rows] == ["/v1/chat/completions", "/v1/embeddings"]


def test_a_workflow_unit_is_one_task_run_in_step_order():
    u = next(u for u in units("support-workflow") if u.group == "T-90103" and u.repeat == 1)
    assert [r["step"] for r in u.rows] == list(range(1, len(u.rows) + 1))


def test_through_the_gateway_the_app_asks_for_a_capability():
    row = units("support-workflow")[0].rows[0]
    path, body = request_for("support-workflow", row, "gateway")
    assert body["model"] == "strong-reasoning" and "reasoning_effort" not in body
    path, body = request_for("support-workflow", row, "direct")
    assert body == row["body"]


def test_direct_replay_uses_the_apps_own_key(sim):
    client = TestClient(sim)
    s = Sender("ticket-triage", "direct", client=client, provsim_url="http://testserver")
    for u in pick("ticket-triage", 3):
        for row in u.rows:
            s.send(*request_for("ticket-triage", row, "direct"), u)
    assert s.status == {200: 6}
    assert "az-key-1" in client.get("/admin/bill").text
    assert "chat-small (gpt-6-luna-2026-09-22) x3" in s.summary()


def test_the_same_seed_picks_the_same_units():
    assert [u.run_id for u in pick("doc-assistant", 5, seed=7)] == [u.run_id for u in pick("doc-assistant", 5, seed=7)]


def test_httpx_is_the_client():
    assert isinstance(Sender("doc-assistant", "direct").client, httpx.Client)
