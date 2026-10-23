import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from larkfield_inspector.server import Inspector, make_server  # noqa: E402
from larkfield_inspector.sources import BUILT_IN  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def truth(name: str) -> dict:
    return json.loads((BUILT_IN / name / "truth.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def app():
    return Inspector("saved", env={})


@pytest.fixture(scope="session")
def server(app):
    srv = make_server(app, "127.0.0.1", 0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def get(url: str, method: str = "GET"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
