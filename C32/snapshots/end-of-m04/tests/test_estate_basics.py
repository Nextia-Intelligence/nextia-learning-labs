"""The estate's command line from the first module: start, look, stop, reset."""

import subprocess
import sys

import httpx
import pytest

from conftest import PROJECT, free_port


def estate(*args, env=None):
    import os

    return subprocess.run([sys.executable, "-m", "estate", *args], cwd=PROJECT, capture_output=True, text=True,
                          env={**os.environ, **(env or {})})


@pytest.mark.services
def test_up_starts_the_simulator_and_down_stops_it(monkeypatch):
    port = str(free_port())
    monkeypatch.setenv("SIM_PORT", port)
    from estate import services

    lines = services.up(["provsim"])
    try:
        assert lines[0].startswith("provsim    up")
        assert httpx.get(f"http://127.0.0.1:{port}/health").json()["recordings"] == 5253
        assert "running" in services.status()[0]
        r = estate("reset")
        assert r.returncode != 0 and "Stop the services first" in r.stderr
    finally:
        down = services.down()
    assert down[0].startswith("provsim    stopped")
    assert services.running() == {}


def test_reset_deletes_the_practice_state(state):
    state.mkdir(parents=True, exist_ok=True)
    (state / "registry.db").write_text("x")
    r = estate("reset")
    assert r.returncode == 0 and not state.exists()


def test_the_commands_are_listed():
    out = estate("--help").stdout
    for command in ("init", "up", "down", "status", "reset"):
        assert command in out
