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

