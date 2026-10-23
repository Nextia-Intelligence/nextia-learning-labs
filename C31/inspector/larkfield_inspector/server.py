"""The inspector's HTTP server: a read-only JSON API and the prebuilt web pages. Standard library only.

It answers GET and HEAD only, on 127.0.0.1 by default. It sends no data anywhere and records nothing:
it has no telemetry of its own and no request log file.
"""

import json
import mimetypes
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, views
from .sources import LiveSource, saved_sources
from .vendor.obs import story as story_module
from .vendor.obs.flags import RULES

PACKAGE = Path(__file__).resolve().parent


def static_folder() -> Path | None:
    for p in (PACKAGE / "static", PACKAGE.parent / "web" / "dist"):
        if (p / "index.html").exists():
            return p
    return None


class Inspector:
    """The data side of the app, without HTTP (the tests use it directly)."""

    def __init__(self, mode: str = "saved", env=os.environ, extra_data: Path | None = None, live=None):
        self.mode = mode
        self.sources = {}
        if mode == "live":
            src = live or LiveSource(env)
            self.sources[src.id] = src
        for src in saved_sources(extra_data):
            self.sources[src.id] = src
        self.default = next(iter(self.sources))
        self.cfg = {"grafana_url": env.get("GRAFANA_URL", "http://127.0.0.1:3031"),
                    "grafana_tempo_uid": env.get("GRAFANA_TEMPO_UID", "tempo"),
                    "langfuse_url": env.get("LANGFUSE_URL", "")}

    def source(self, q: dict):
        ident = q.get("ds") or self.default
        if ident not in self.sources:
            raise LookupError(f"There is no data set {ident!r}. Use one of: {', '.join(self.sources)}.")
        return self.sources[ident]

    def run_of(self, src, run_id: str):
        run = src.find(run_id)
        if run is None:
            raise LookupError(f"There is no run {run_id!r} in the data set {src.id!r}.")
        return run

    # ------------------------------------------------------------ endpoints
    def info(self, q: dict) -> dict:
        sets = []
        for s in self.sources.values():
            sets.append({"id": s.id, "mode": s.mode, "about": s.about,
                         "audit": s.audit.exists(), "error": getattr(s, "error", "")})
        return {"version": __version__, "mode": self.mode, "default": self.default, "datasets": sets,
                "flags": list(RULES), "budget_per_resolved": views.BUDGET_PER_RESOLVED, "tz_hours": views.TZ_HOURS,
                "links": {"grafana": bool(self.cfg["grafana_url"]), "langfuse": bool(self.cfg["langfuse_url"])}}

    def runs(self, q: dict) -> dict:
        src = self.source(q)
        out = views.runs_view(list(src.runs.values()), q)
        out["dataset"] = src.id
        out["error"] = getattr(src, "error", "")
        return out

    def run(self, run_id: str, q: dict) -> dict:
        src = self.source(q)
        run = self.run_of(src, run_id)
        same = [r.run_id for r in src.runs.values() if r.ticket == run.ticket and r.ticket]
        out = views.run_detail(run, self.cfg, same, story_module.people())
        out["dataset"] = src.id
        return out

    def audit(self, run_id: str, q: dict) -> dict:
        src = self.source(q)
        records, verified = src.audit.load()
        if not src.audit.exists():
            raise LookupError("This data set has no audit store file (set AUDIT_STORE in live mode).")
        out = views.audit_view(records, verified, run_id, story_module.people(), story_module.sentence)
        if not out["records"]:
            raise LookupError(f"There are no audit records for the run {run_id!r}.")
        out["dataset"] = src.id
        out["store"] = src.audit.path.name
        return out

    def audit_markdown(self, run_id: str, q: dict) -> tuple[str, str]:
        src = self.source(q)
        if not src.audit.exists():
            raise LookupError("This data set has no audit store file.")
        text = story_module.story(src.audit.store(), run_id, markdown=True)
        if text.startswith("No audit records"):
            raise LookupError(text)
        ticket = next((r["event"]["ticket_id"] for r in src.audit.load()[0] if r["event"]["run_id"] == run_id), "")
        name = f"audit-{ticket + '-' if ticket else ''}{run_id}.md"
        return text + "\n", name

    def cost(self, q: dict) -> dict:
        src = self.source(q)
        out = views.cost_view(list(src.runs.values()), q)
        out["dataset"] = src.id
        if src.mode == "live":
            out["prometheus"] = src.cost_series()
        return out

    def compare(self, q: dict) -> dict:
        src = self.source(q)
        a, b = q.get("a"), q.get("b")
        if not a or not b:
            pair = views.default_compare(src.runs)
            if pair is None:
                raise LookupError("There is no ticket with two runs in this data set.")
            a, b = pair
        out = views.compare_view(self.run_of(src, a), self.run_of(src, b))
        tickets = {}
        for r in src.runs.values():
            tickets.setdefault(r.ticket, []).append(r.run_id)
        out["tickets"] = {k: v for k, v in sorted(tickets.items()) if len(v) > 1}
        out["dataset"] = src.id
        return out

    def refresh(self, q: dict) -> dict:
        src = self.source(q)
        src.refresh()
        return {"ok": True, "dataset": src.id}


ROUTES = [
    (re.compile(r"^/api/info$"), "info"),
    (re.compile(r"^/api/runs$"), "runs"),
    (re.compile(r"^/api/runs/(?P<run_id>[^/]+)$"), "run"),
    (re.compile(r"^/api/runs/(?P<run_id>[^/]+)/audit$"), "audit"),
    (re.compile(r"^/api/runs/(?P<run_id>[^/]+)/audit\.md$"), "audit_markdown"),
    (re.compile(r"^/api/cost$"), "cost"),
    (re.compile(r"^/api/compare$"), "compare"),
    (re.compile(r"^/api/refresh$"), "refresh"),
]

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                               "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def make_handler(app: Inspector, static: Path | None):
    class Handler(BaseHTTPRequestHandler):
        def version_string(self):
            return "larkfield-inspector/" + __version__

        def log_message(self, format, *args):   # no request log: the inspector records nothing
            return

        def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in {**SECURITY_HEADERS, **(extra or {})}.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, obj):
            body = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8", {"Cache-Control": "no-store"})

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[-1] for k, v in parse_qs(url.query).items()}
            if url.path.startswith("/api/"):
                return self._api(url.path, q)
            return self._static(url.path)

        def _not_allowed(self):
            self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "The inspector is read-only: GET only."})

        do_POST = do_PUT = do_DELETE = do_PATCH = _not_allowed

        def _api(self, path: str, q: dict):
            for pattern, name in ROUTES:
                m = pattern.match(path)
                if not m:
                    continue
                try:
                    result = getattr(app, name)(*m.groupdict().values(), q)
                except LookupError as e:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": str(e).strip("'\"")})
                except ValueError as e:
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})
                if name == "audit_markdown":
                    text, filename = result
                    return self._send(HTTPStatus.OK, text.encode("utf-8"), "text/markdown; charset=utf-8",
                                      {"Content-Disposition": f'attachment; filename="{filename}"',
                                       "Cache-Control": "no-store"})
                return self._json(HTTPStatus.OK, result)
            return self._json(HTTPStatus.NOT_FOUND, {"error": f"No API path {path}."})

        def _static(self, path: str):
            if static is None:
                body = ("<!doctype html><meta charset=utf-8><title>Run inspector</title>"
                        "<p>The web pages are missing (web/dist). The API works: <a href=/api/info>/api/info</a>.")
                return self._send(HTTPStatus.OK, body.encode(), "text/html; charset=utf-8")
            rel = path.lstrip("/") or "index.html"
            root = static.resolve()
            target = (static / rel).resolve()
            if root not in target.parents or not target.is_file():
                target = static / "index.html"   # the app's own routes (#/run/...) all load index.html
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
                ctype += "; charset=utf-8"
            cache = "no-cache" if target.name == "index.html" else "public, max-age=31536000, immutable"
            self._send(HTTPStatus.OK, target.read_bytes(), ctype, {"Cache-Control": cache})

    return Handler


def make_server(app: Inspector, host: str = "127.0.0.1", port: int = 8318) -> ThreadingHTTPServer:
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("image/svg+xml", ".svg")
    server = ThreadingHTTPServer((host, port), make_handler(app, static_folder()))
    server.daemon_threads = True
    return server
