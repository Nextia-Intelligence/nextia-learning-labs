"""The weekly digest script: constructed, small and real. Nobody registered it."""

import sys

from conftest import PROJECT
from provsim.store import Store

sys.path.insert(0, str(PROJECT / "apps" / "digest"))
import weekly_digest  # noqa: E402


def test_the_digest_sends_forty_customer_messages_to_fernway():
    body = weekly_digest.digest_request(weekly_digest.week_messages())
    assert body["model"] == "fernway-swift" and len(weekly_digest.week_messages()) == 40
    assert "Order LK-104233" in body["messages"][1]["content"]       # customer data in the prompt


def test_its_answer_is_the_one_constructed_recording(sim_client):
    body = weekly_digest.digest_request(weekly_digest.week_messages())
    answers = Store().answers(body)
    assert len(answers) == 1 and answers[0].constructed
    r = sim_client.post("/fernway/v1/chat/completions", json=body,
                        headers={"Authorization": f"Bearer {weekly_digest.FERNWAY_KEY}", "x-sim-host": "build-runner-3"})
    assert r.status_code == 200 and r.headers["x-sim-constructed"] == "true"
    assert ",build-runner-3,api.fernway.example,fernway,fw-7Q2K,200," in sim_client.get("/admin/egress").text
