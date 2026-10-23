"""Shared test fixtures. The tests never touch your state/ folder: each test gets its own, in a temporary folder.
No test calls a real provider: the provider simulator runs in the same process (or on a free port)."""

import os
import socket
import tempfile
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent.parent
os.environ.setdefault("RESOLVER_WORK", tempfile.mkdtemp(prefix="estate-tests-work-"))


@pytest.fixture(autouse=True)
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("ESTATE_STATE", str(tmp_path / "state"))
    monkeypatch.delenv("ESTATE_ACTOR", raising=False)
    try:
        from estate import clock

        clock.set_replay_time(None)
    except ImportError:
        pass
    return tmp_path / "state"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def sim(tmp_path):
    """The provider simulator, in this process."""
    from provsim.app import create_app

    return create_app(state_dir=tmp_path / "provider", speed=0.0, egress="open")


@pytest.fixture
def sim_client(sim):
    from starlette.testclient import TestClient

    return TestClient(sim)


def stream(name: str) -> list[dict]:
    import gzip
    import json

    with gzip.open(PROJECT / "apps" / "streams" / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class Estate:
    """The estate's apps registered from registrations/ (high risk reviewed), the configuration published and
    each app's credentials issued: the state at the end of the registration module."""

    def __init__(self, ids=None):
        from estate import configstore, identity, registry

        self.registry, self.identity, self.configstore = registry, identity, configstore
        forms = {p.stem: registry.read_form(p) for p in sorted((PROJECT / "registrations").glob("*.yaml"))}
        self.secrets = {}
        for agent_id, form in forms.items():
            if ids and agent_id not in ids:
                continue
            reg = registry.register(form, "usr-kwame")
            if reg.status == "pending":
                registry.review(agent_id, "usr-kwame", form["review_date"], note="test review")
            if form["kind"] != "tool-server":
                self.secrets[agent_id] = identity.issue_credentials(agent_id, "usr-kwame")[1]
        configstore.publish("usr-kwame", "tests")

    def token(self, agent_id: str, audience: str = "model-gateway") -> str:
        return self.identity.token(agent_id, self.secrets[agent_id], audience)["access_token"]

    def snapshot(self, replica: str = "a") -> dict:
        return self.configstore.snapshot(replica)


@pytest.fixture
def estate():
    return Estate()


@pytest.fixture
def gateway(estate, sim):
    """make(...) -> a TestClient of one gateway replica, its upstream the in-process simulator."""
    import httpx
    from starlette.testclient import TestClient

    from gateway.app import create_app
    from gateway.config import ConfigCache

    made = []

    def make(replica="a", snapshot=None, cache=None):
        if cache is None:
            cache = ConfigCache(replica)
            cache.set(snapshot or estate.snapshot(replica))
        app = create_app(replica, cache=cache, secrets={"azure": "sim-az-gateway-0009"},
                         transport=httpx.ASGITransport(app=sim), provsim_url="http://sim")
        c = TestClient(app)
        c.__enter__()
        made.append(c)
        return c

    yield make
    for c in made:
        c.__exit__(None, None, None)
