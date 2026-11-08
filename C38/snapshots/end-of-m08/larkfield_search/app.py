"""The ready-made search page: a small web server from Python's standard library, on this computer only.

    search serve --port 8038 --run ltr      then open http://127.0.0.1:8038/

GET /                   the page (static/search.html)
GET /api/search?q=...   {"run", "query", "ms", "results": [...], "facets": {...}}
GET /api/suggest?q=...  {"suggestions": [...]}
GET /health             {"status": "ok", "products": n}
"""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import data, facets, runs, suggest

PAGE = Path(__file__).resolve().parent / "static" / "search.html"


def search_json(q, run, k=20):
    t0 = time.perf_counter()
    res = runs.get(run)(q, None, 100) if q.strip() else []
    ms = (time.perf_counter() - t0) * 1000
    cat = data.catalogue().set_index("product_id")
    items = []
    for pid, score in res[:k]:
        r = cat.loc[pid]
        items.append({"product_id": pid, "title": r["title"], "product_class": r["product_class"],
                      "price": float(r["price"]), "in_stock": bool(r["in_stock"]), "on_sale": bool(r["on_sale"]),
                      "score": round(float(score), 4)})
    return {"run": run, "query": q, "ms": round(ms, 1), "results": items,
            "facets": facets.facets([p for p, _ in res]) if res else {}}


def handler(run):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, kind="application/json"):
            b = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", f"{kind}; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query).get("q", [""])[0]
            if u.path == "/":
                self.send(200, PAGE.read_bytes(), "text/html")
            elif u.path == "/api/search":
                self.send(200, json.dumps(search_json(q, run)))
            elif u.path == "/api/suggest":
                self.send(200, json.dumps({"suggestions": [t for t, _ in suggest.suggest(q)]}))
            elif u.path == "/health":
                self.send(200, json.dumps({"status": "ok", "products": len(data.catalogue())}))
            else:
                self.send(404, json.dumps({"error": "not found"}))
    return H


def serve(port=8038, run="ltr"):
    runs.get(run)("warm up", None, 10)
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler(run))
    print(f"Larkfield search page: http://127.0.0.1:{port}/  (run {run}; stop with Ctrl+C)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
