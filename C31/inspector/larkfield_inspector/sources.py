"""Where the runs come from: a folder of saved telemetry (saved mode) or Tempo's HTTP API (live mode).

Both give the same thing: spans (vendor/obs/model.py's Span), grouped into runs by the same function,
with the same five flags (vendor/obs/flags.py), and an audit store file. Nothing here writes anywhere:
live mode only sends GET requests to the addresses in the environment variables.
"""

import base64
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .vendor.auditstore.store import AuditStore
from .vendor.obs.flags import flag_run
from .vendor.obs.model import Span, Telemetry, attributes, group_runs

PACKAGE = Path(__file__).resolve().parent
BUILT_IN = PACKAGE / "data"
SAVED = [  # id, folder name, what it is
    ("week", "week", "replayed_week"),
    ("healthy-week", "healthy-week", "healthy_week"),
    ("constructed", "constructed", "constructed"),
]


class AuditFile:
    """The audit store file, read again only when the file changes."""

    def __init__(self, path: Path | None):
        self.path = Path(path) if path else None
        self._stamp = None
        self._records: list = []
        self._verify: dict = {}
        self._lock = threading.Lock()

    def exists(self) -> bool:
        return bool(self.path and self.path.exists())

    def load(self) -> tuple[list, dict]:
        if not self.exists():
            return [], {"ok": False, "count": 0, "head": "", "problems": ["no audit store file"]}
        store = AuditStore(self.path)
        stamp = tuple((p.stat().st_mtime_ns, p.stat().st_size) if p.exists() else None
                      for p in (self.path, store.anchor))
        with self._lock:
            if stamp != self._stamp:
                self._records, self._verify, self._stamp = store.records(), store.verify(), stamp
            return self._records, self._verify

    def store(self) -> AuditStore:
        return AuditStore(self.path)


class SavedSource:
    """One folder of saved telemetry (the files that the course's workflow or the Collector writes)."""

    mode = "saved"

    def __init__(self, ident: str, folder: Path, about: str):
        self.id, self.folder, self.about = ident, Path(folder), about
        self.audit = AuditFile(self.folder / "audit.jsonl")
        self._telemetry = None
        self._lock = threading.Lock()

    @property
    def runs(self) -> dict:
        with self._lock:
            if self._telemetry is None:
                self._telemetry = Telemetry(self.folder)
            return self._telemetry.runs

    def find(self, key: str):
        self.runs
        return self._telemetry.find(key)

    def refresh(self):
        return None


# ------------------------------------------------------------------ live mode: Tempo's HTTP API

def hex_id(value: str | None, size: int) -> str:
    """A trace or span ID as lower-case hex. Tempo's OTLP JSON has base64 IDs; the OTLP files have hex."""
    if not value:
        return ""
    v = value.strip()
    if len(v) == size * 2 and all(c in "0123456789abcdefABCDEF" for c in v):
        return v.lower()
    try:
        raw = base64.b64decode(v + "=" * (-len(v) % 4), validate=False)
    except ValueError:
        return v.lower()
    if len(raw) == size:
        return raw.hex()
    if len(v) < size * 2 and all(c in "0123456789abcdefABCDEF" for c in v):
        return v.lower().rjust(size * 2, "0")   # Tempo's search answer drops the leading zeros
    return raw.hex() if raw else v.lower()


KINDS = {0: "unspecified", 1: "internal", 2: "server", 3: "client", 4: "producer", 5: "consumer"}
STATUS = {0: "", 1: "ok", 2: "error", "STATUS_CODE_UNSET": "", "STATUS_CODE_OK": "ok", "STATUS_CODE_ERROR": "error"}


def _kind(value) -> str:
    if isinstance(value, int):
        return KINDS.get(value, "")
    return str(value or "").replace("SPAN_KIND_", "").lower()


def resource_spans(doc: dict) -> list:
    """The resourceSpans of a trace answer, in any of Tempo's shapes."""
    if "trace" in doc and isinstance(doc["trace"], dict):   # /api/v2/traces/<id>
        doc = doc["trace"]
    return doc.get("resourceSpans") or doc.get("batches") or []


def spans_from_otlp(doc: dict) -> list[Span]:
    """OTLP JSON (Tempo's answer or one line of the Collector's file) -> spans, as model.load_spans does."""
    spans = []
    for rs in resource_spans(doc):
        service = attributes(rs.get("resource", {}).get("attributes")).get("service.name", "")
        for ss in rs.get("scopeSpans") or rs.get("instrumentationLibrarySpans") or []:
            for s in ss.get("spans", []):
                status = s.get("status", {}) or {}
                spans.append(Span(
                    trace_id=hex_id(s.get("traceId"), 16), span_id=hex_id(s.get("spanId"), 8),
                    parent_id=hex_id(s.get("parentSpanId"), 8), name=s.get("name", ""), kind=_kind(s.get("kind")),
                    start=int(s.get("startTimeUnixNano", 0)), end=int(s.get("endTimeUnixNano", 0)),
                    attrs=attributes(s.get("attributes")),
                    status=STATUS.get(status.get("code", ""), ""),
                    status_message=status.get("message", ""),
                    links=[(hex_id(link.get("traceId"), 16), hex_id(link.get("spanId"), 8),
                            attributes(link.get("attributes"))) for link in s.get("links", []) or []],
                    service=service))
    return spans


class LiveRuns:
    """The same object as Telemetry for the views: runs with their flags, and find()."""

    def __init__(self, spans: list[Span]):
        self.spans = spans
        self.runs = group_runs(spans)
        for run in self.runs.values():
            run.flags = flag_run(run)

    def find(self, key: str):
        if key in self.runs:
            return self.runs[key]
        for run in self.runs.values():
            if key in run.trace_ids:
                return run
        matches = [r for r in self.runs.values() if r.ticket == key]
        return matches[-1] if matches else None


def http_get(url: str, timeout: float = 10.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:   # noqa: S310 (the user's own local services)
        return json.loads(resp.read().decode("utf-8"))


class Tempo:
    QUERY = '{ span.gen_ai.operation.name =~ "invoke_agent|invoke_workflow|approve" }'

    def __init__(self, url: str, get=http_get):
        self.url = url.rstrip("/")
        self.get = get

    def search(self, start_s: int, end_s: int, limit: int, query: str | None = None) -> list[str]:
        params = urllib.parse.urlencode({"q": query or self.QUERY, "start": start_s, "end": end_s, "limit": limit})
        doc = self.get(f"{self.url}/api/search?{params}")
        return [hex_id(t.get("traceID") or t.get("traceId"), 16) for t in doc.get("traces", [])]

    def trace(self, trace_id: str) -> dict:
        return self.get(f"{self.url}/api/traces/{trace_id}")


class Prometheus:
    QUERY = "sum(increase(larkfield_run_cost_total[1h]))"

    def __init__(self, url: str, get=http_get):
        self.url = url.rstrip("/")
        self.get = get

    def cost_series(self, start_s: int, end_s: int, query: str | None = None, step: int = 3600) -> list:
        params = urllib.parse.urlencode({"query": query or self.QUERY, "start": start_s, "end": end_s, "step": step})
        doc = self.get(f"{self.url}/api/v1/query_range?{params}")
        out = []
        for result in doc.get("data", {}).get("result", []):
            out.append({"labels": result.get("metric", {}),
                        "points": [[int(float(t) * 1000), float(v)] for t, v in result.get("values", [])]})
        return out


class LiveSource:
    """Live mode: runs from Tempo (read-only), the audit store file, and cost per hour from Prometheus."""

    mode = "live"
    id = "live"
    about = "live"

    def __init__(self, env=os.environ, get=http_get):
        self.tempo = Tempo(env.get("TEMPO_URL", "http://127.0.0.1:3200"), get)
        self.prometheus = Prometheus(env.get("PROMETHEUS_URL", "http://127.0.0.1:9090"), get)
        self.query = env.get("TEMPO_QUERY") or None
        self.cost_query = env.get("PROMETHEUS_COST_QUERY") or None
        self.hours = float(env.get("INSPECTOR_LIVE_HOURS", "168"))
        self.limit = int(env.get("TEMPO_LIMIT", "500"))
        self.ttl = float(env.get("INSPECTOR_LIVE_TTL", "30"))
        self.audit = AuditFile(Path(env["AUDIT_STORE"]) if env.get("AUDIT_STORE") else None)
        self.now = time.time
        self._data: LiveRuns | None = None
        self._loaded_at = 0.0
        self.error = ""
        self._lock = threading.Lock()

    def window(self) -> tuple[int, int]:
        end = int(self.now())
        return end - int(self.hours * 3600), end

    def load(self) -> LiveRuns:
        start, end = self.window()
        ids = self.tempo.search(start, end, self.limit, self.query)
        spans, seen = [], set()
        for trace_id in ids:
            if trace_id in seen:
                continue
            seen.add(trace_id)
            spans.extend(spans_from_otlp(self.tempo.trace(trace_id)))
        # a run's second trace (the decision) is found by the search too; a missing one only shortens the run
        return LiveRuns(spans)

    @property
    def runs(self) -> dict:
        with self._lock:
            if self._data is None or self.now() - self._loaded_at > self.ttl:
                try:
                    self._data = self.load()
                    self.error = ""
                except Exception as e:   # Tempo is not running, or answers something else
                    self.error = f"{type(e).__name__}: {e}"
                    if self._data is None:
                        self._data = LiveRuns([])
                self._loaded_at = self.now()
            return self._data.runs

    def find(self, key: str):
        self.runs
        return self._data.find(key)

    def refresh(self):
        with self._lock:
            self._loaded_at = 0.0

    def cost_series(self) -> dict:
        start, end = self.window()
        try:
            return {"available": True, "query": self.cost_query or Prometheus.QUERY,
                    "series": self.prometheus.cost_series(start, end, self.cost_query)}
        except Exception as e:
            return {"available": False, "query": self.cost_query or Prometheus.QUERY, "error": f"{type(e).__name__}: {e}"}


def saved_sources(extra: Path | None = None) -> list:
    out = [SavedSource(ident, BUILT_IN / folder, about) for ident, folder, about in SAVED
           if (BUILT_IN / folder).exists()]
    if extra:
        out.insert(0, SavedSource("yours", Path(extra), "your_data"))
    return out
