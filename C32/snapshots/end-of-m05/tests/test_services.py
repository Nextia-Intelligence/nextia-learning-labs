"""The whole estate as real processes on free ports: the workflow through both gateways, and a replica that stops."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest

from conftest import PROJECT, free_port

pytestmark = pytest.mark.services


@pytest.fixture(scope="module")
def estate_up():
    from estate import services

    root = Path(tempfile.mkdtemp(prefix="estate-services-"))
    env = {"ESTATE_STATE": str(root / "state"), "SIM_PORT": str(free_port()), "ESTATE_PORT": str(free_port()),
           "GATEWAY_PORT": str(free_port()), "TOOLGATE_PORT": str(free_port())}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    replica_ports = {r: free_port() for r in "abc"}
    real_ports = services.ports

    def ports():
        p = real_ports()
        p.update({f"replica-{r}": port for r, port in replica_ports.items()})
        return p

    services.ports = ports
    py = sys.executable

    def run(*args):
        return subprocess.run([py, "-m", "estate", *args], cwd=PROJECT, env={**os.environ}, capture_output=True,
                              text=True, check=True).stdout

    run("init")
    for f in sorted((PROJECT / "registrations").glob("*.yaml")):
        run("register", str(f))
    for a in ("support-workflow", "support-mcp", "orders-mcp"):
        run("review", a, "--next", "2026-12-01")
    for a in ("ticket-triage", "support-workflow"):
        run("credentials", "issue", a)
    lines = services.up()
    assert all(" up " in line for line in lines), lines
    p = ports()
    urls = {"front": f"http://127.0.0.1:{p['front']}", "tools": f"http://127.0.0.1:{p['toolgate']}",
            "control": f"http://127.0.0.1:{p['control']}", "provsim": f"http://127.0.0.1:{p['provsim']}"}
    yield {"env": {**os.environ}, "urls": urls, "services": services, "run": run, "root": root}
    services.down()
    services.ports = real_ports
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def resolver(env, urls, *args):
    e = {**env, "RESOLVER_PROVIDER": "gateway", "RESOLVER_TOOLS": "gateway", "ESTATE_URL": urls["control"],
         "ESTATE_GATEWAY_URL": urls["front"] + "/v1", "ESTATE_TOOLS_URL": urls["tools"]}
    return subprocess.run([sys.executable, "-m", "resolver", *args], cwd=PROJECT, env=e, capture_output=True,
                          text=True).stdout


def test_the_workflow_runs_through_both_gateways_and_a_person_approves(estate_up, monkeypatch):
    env, urls = estate_up["env"], estate_up["urls"]
    out = resolver(env, urls, "run", "T-90103", "--variant", "agent_structured", "--model", "strong-reasoning")
    assert "Outcome: resolve (rule W5) | 2 model call(s), 1 tool call(s) | 4647 tokens in, 266 out" in out
    run_id = "T-90103-agent_structured-strong-reasoning-1"
    out = resolver(env, urls, "approve", run_id, "--as", "agent", "--approver", "usr-omar")
    assert out == ""                                     # refused by the platform (stderr): nothing saved
    out = resolver(env, urls, "approve", run_id, "--as", "agent", "--approver", "usr-sam")
    assert "Approval grant from the platform for usr-sam" in out and "Status: done" in out
    monkeypatch.setenv("ESTATE_STATE", env["ESTATE_STATE"])
    from estate.usage import UsageStore

    store = UsageStore(Path(env["ESTATE_STATE"]) / "usage.db")
    assert store.rows("select count(*) n from model_calls where agent_id = 'support-workflow'")[0]["n"] == 2
    writes = store.rows("select tool, approver from tool_calls where kind = 'write' and outcome = 'ok' order by id")
    assert [w["tool"] for w in writes] == ["reship_item", "create_return_label", "add_ticket_note"]
    assert writes[0]["approver"] == "usr-sam"


def test_calls_go_on_when_one_replica_stops(estate_up, monkeypatch):
    from apps.client import Sender
    from apps.replay import pick, request_for

    env, urls = estate_up["env"], estate_up["urls"]
    monkeypatch.setenv("ESTATE_STATE", env["ESTATE_STATE"])
    pids = json.loads((Path(env["ESTATE_STATE"]) / "pids.json").read_text())
    os.kill(pids["replica-b"], signal.SIGTERM)
    time.sleep(0.5)
    client = httpx.Client(timeout=30)
    s = Sender("ticket-triage", "gateway", client=client, gateway_url=urls["front"] + "/v1", estate_url=urls["control"])
    for u in pick("ticket-triage", 10):
        for row in u.rows:
            s.send(*request_for("ticket-triage", row, "gateway"), u)
    assert s.status == {200: 20}
    status = client.get(urls["front"] + "/front/status").json()
    assert status["healthy"]["b"] is False
