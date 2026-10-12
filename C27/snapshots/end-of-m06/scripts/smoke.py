"""Smoke test of a running assistant: the core journey, from outside, in a few seconds (Module 6).

    python scripts/smoke.py http://127.0.0.1:8000
    SMOKE_TOKEN=$(python -m idp token usr-sam) python scripts/smoke.py http://127.0.0.1:8000

Standard library only, so it runs anywhere (a CI job, a fresh computer). Without SMOKE_TOKEN it
checks what needs no sign-in; with it, it also asks one question and checks the citation.
Exit code 0 = every check passed.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def call(base: str, path: str, token: str = "", body: dict | None = None) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method="POST" if data else "GET")
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode()
            status = r.status
    except urllib.error.HTTPError as e:
        text, status = e.read().decode(), e.code
    except urllib.error.URLError as e:
        return 0, {"code": "unreachable", "message": str(e.reason)}
    try:
        return status, json.loads(text)
    except json.JSONDecodeError:
        return status, text


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
    token = os.environ.get("SMOKE_TOKEN", "")
    checks = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name}{'  (' + detail + ')' if detail else ''}")

    s, b = call(base, "/health")
    check("health", s == 200 and b.get("status") == "ok", f"version {b.get('version') if s == 200 else s}")
    s, b = call(base, "/ready")
    check("ready: database and migrations", s == 200, json.dumps(b) if s != 200 else b.get("answer_provider", ""))
    s, b = call(base, "/app/")
    check("the page is served", s == 200 and "Document assistant" in str(b))
    s, b = call(base, "/v1/tenants/larkfield/documents")
    check("no sign-in -> 401", s == 401 and b.get("code") == "unauthenticated")
    if token:
        s, b = call(base, "/v1/tenants/larkfield/documents", token)
        indexed = b.get("counts", {}).get("indexed", 0) if s == 200 else 0
        check("documents are indexed", s == 200 and indexed > 0, f"{indexed} indexed")
        s, b = call(base, "/v1/tenants/larkfield/answers", token,
                    {"question": "A customer was charged twice for the same order. How quickly do we refund the "
                                 "extra charge?", "as_of": "2026-10-09"})
        a = b.get("answer", {}) if s == 200 else {}
        cited = [c for claim in a.get("claims", []) for c in claim["citations"]]
        check("a question gets a cited answer", s == 200 and a.get("answerable") and bool(cited),
              f"{a.get('provider')}: {a.get('answer', b)!s:.80}")
        s, b = call(base, "/v1/tenants/bramble/documents", token)
        check("another shop -> 404", s == 404)
    print(f"{sum(checks)} of {len(checks)} checks passed.")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
