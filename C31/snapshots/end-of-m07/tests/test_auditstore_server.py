"""The audit store's door: OTLP/HTTP JSON (gzip too); a bad event is kept apart, never answered with 400."""

import gzip
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from auditstore.server import make_handler
from auditstore.store import AuditStore
from tests.test_audit import event


def request(events):
    recs = [{"eventName": f"larkfield.audit.{e.get('type', 'x')}", "body": {"stringValue": json.dumps(e)},
             "attributes": [{"key": "audit.type", "value": {"stringValue": e.get("type", "x")}}]} for e in events]
    return {"resourceLogs": [{"scopeLogs": [{"logRecords": recs}]}]}


def post(port, body: bytes, gz=False):
    headers = {"Content-Type": "application/json", **({"Content-Encoding": "gzip"} if gz else {})}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/logs", data=gzip.compress(body) if gz else body,
                                 headers=headers, method="POST")
    return urllib.request.urlopen(req).status


def test_events_are_appended_and_bad_ones_kept_apart(tmp_path):
    store = AuditStore(tmp_path / "audit.jsonl")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        assert post(port, json.dumps(request([event(1), event(2)])).encode(), gz=True) == 200
        bad = event(3, action={"reply": "text"})
        assert post(port, json.dumps(request([bad])).encode()) == 200
    finally:
        server.shutdown()
    assert store.verify()["count"] == 2 and store.verify()["ok"]
    assert "text fields" in store.rejected.read_text()
