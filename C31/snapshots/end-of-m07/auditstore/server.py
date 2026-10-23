"""The audit store's door: receives audit events from the Collector, as OTLP/HTTP logs, and appends them.

    python -m auditstore serve [--port 8313] [--store work/audit/audit.jsonl]

It accepts POST /v1/logs with OTLP JSON (the Collector's otlp_http exporter with `encoding: json`) or OTLP
protobuf (gzip or not). Every log record whose event name starts with larkfield.audit. must carry the audit
event as its body; the server checks it (auditstore/schema.py) and appends it to the hash-chained store. An
event that fails the check is NOT refused with HTTP 400 (the Collector drops a batch that gets a 400 and does
not retry it: an audit event would be lost); it is kept in a separate file (audit.rejected.jsonl) for a person. There is no read, update or delete endpoint: reading is done on the file, with
other access rights (python -m obs audit verify | show | story).
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from auditstore.schema import AuditEventError  # noqa: E402
from auditstore.store import AuditStore  # noqa: E402


def records_from_json(body: bytes) -> list[tuple[str, str]]:
    """(event name, body text) of every log record in an OTLP JSON logs request."""
    out = []
    data = json.loads(body or b"{}")
    for rl in data.get("resourceLogs", []):
        for sl in rl.get("scopeLogs", []):
            for r in sl.get("logRecords", []):
                name = r.get("eventName", "")
                attrs = {a["key"]: a.get("value", {}).get("stringValue") for a in r.get("attributes", [])}
                if not name and attrs.get("audit.type"):
                    name = f"larkfield.audit.{attrs['audit.type']}"
                out.append((name, r.get("body", {}).get("stringValue", "")))
    return out


def records_from_protobuf(body: bytes) -> list[tuple[str, str]]:
    from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
    req = ExportLogsServiceRequest()
    req.ParseFromString(body)
    out = []
    for rl in req.resource_logs:
        for sl in rl.scope_logs:
            for r in sl.log_records:
                name = r.event_name
                if not name:
                    for a in r.attributes:
                        if a.key == "audit.type":
                            name = f"larkfield.audit.{a.value.string_value}"
                out.append((name, r.body.string_value))
    return out


def make_handler(store: AuditStore):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):   # no request log: the events are the record
            pass

        def _answer(self, code: int, obj: dict):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/ready":
                return self._answer(200, {"ready": True, "records": store.verify()["count"]})
            self._answer(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/v1/logs":
                return self._answer(404, {"error": "only POST /v1/logs"})
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            if (self.headers.get("Content-Encoding") or "").lower() == "gzip":
                import gzip
                body = gzip.decompress(body)
            try:
                if "json" in (self.headers.get("Content-Type") or ""):
                    recs = records_from_json(body)
                else:
                    recs = records_from_protobuf(body)
            except (ValueError, KeyError) as e:   # not OTLP at all: the sender has a bug
                print(f"refused: {e}", file=sys.stderr, flush=True)
                return self._answer(400, {"error": str(e)})
            rejected = 0
            for name, text in recs:
                try:
                    if not name.startswith("larkfield.audit."):
                        raise AuditEventError(f"not an audit event: {name or 'no event name'}")
                    store.append(json.loads(text))
                except (AuditEventError, ValueError) as e:
                    # Never answer 400 for one bad event: the Collector DROPS a batch that gets a 400 (it retries
                    # only 429 and 5xx). The bad event is kept apart, for a person to look at.
                    store.reject(text, str(e))
                    rejected += 1
                except OSError as e:   # the store cannot write: 503, so that the Collector sends it again
                    print(f"cannot store: {e}", file=sys.stderr, flush=True)
                    return self._answer(503, {"error": "the audit store cannot write now"})
            if rejected:
                print(f"{rejected} event(s) kept in {store.rejected.name}: they do not pass the schema", file=sys.stderr, flush=True)
            self._answer(200, {"partialSuccess": {}})

    return Handler


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m auditstore")
    ap.add_argument("command", choices=["serve"])
    ap.add_argument("--port", type=int, default=int(os.environ.get("AUDIT_PORT", "8313")))
    ap.add_argument("--host", default=os.environ.get("AUDIT_HOST", "127.0.0.1"))
    ap.add_argument("--store", default=os.environ.get("OBS_AUDIT", str(PROJECT / "work" / "audit" / "audit.jsonl")))
    args = ap.parse_args(argv)
    store = AuditStore(Path(args.store))
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store))
    print(f"Audit store: http://{args.host}:{args.port}/v1/logs -> {store.path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
