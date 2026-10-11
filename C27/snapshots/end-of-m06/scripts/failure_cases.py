"""Run the four failure cases of Module 4 for real, and show what the user gets in each.

    python -m scripts.failure_cases
    python -m scripts.failure_cases --json

1. wrong shop:       Ines (Bramble Books) asks a question in Larkfield's assistant
2. missing source:   a question whose document was deleted, and one that no document answers
3. invalid file:     a PDF cut during the upload, a Word file, a file over the size limit
4. provider timeout: a practice provider that answers after 30 seconds (scripts/fake_provider.py),
                     with a 2-second timeout and 2 retries
The API runs in this process with practice tokens. The changes are undone at the end: the
deleted document is uploaded and indexed again, the bad uploads are deleted.
"""

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from doc_assistant.config import settings as load_settings
from doc_assistant.main import create_app
from doc_assistant.providers import LiveProvider
from doc_assistant.worker import drain

from .fake_provider import FakeProvider
from .practice import practice_tokens

DATA = Path(__file__).resolve().parent.parent / "data"


def show(case: str, r, took: float) -> dict:
    body = r.json()
    if "answer" in body:
        a = body["answer"]
        brief = {"answerable": a["answerable"], "answer": a["answer"], "provider": a["provider"]}
    elif "document" in body:
        d = body["document"]
        brief = {"status": d["status"], "error": d.get("error")}
    else:
        brief = {"code": body.get("code"), "message": body.get("message")}
    return {"case": case, "status": r.status_code, "seconds": round(took, 2), **brief}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.failure_cases")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    token, validator = practice_tokens()
    s = load_settings()
    app = create_app(replace(s, trace_file=""), start_worker=False)
    out = []
    with TestClient(app) as client:
        app.state.validator = validator
        ines, grace = token("usr-ines"), token("usr-grace")

        def call(case, method, path, headers, **kw):
            start = time.monotonic()
            r = client.request(method, path, headers=headers, **kw)
            out.append(show(case, r, time.monotonic() - start))
            return r

        # 1. wrong shop
        call("wrong shop: Ines asks at Larkfield", "POST", "/v1/tenants/larkfield/answers", ines,
             json={"question": "What is the staff discount?"})
        call("wrong shop: a shop that does not exist", "POST", "/v1/tenants/acme/answers", ines,
             json={"question": "What is the staff discount?"})
        # 2. missing source
        call("missing source: no document answers", "POST", "/v1/tenants/bramble/answers", ines,
             json={"question": "Do we sell e-books?"})
        docs = client.get("/v1/tenants/bramble/documents", headers=ines).json()["documents"]
        gift = next(d for d in docs if d["doc_key"] == "gift-cards")
        call("missing source: delete the gift card policy", "DELETE",
             f"/v1/tenants/bramble/documents/{gift['document_id']}", ines)
        call("missing source: ask about gift cards again", "POST", "/v1/tenants/bramble/answers", ines,
             json={"question": "How long is a gift card valid?"})
        with open(DATA / "bramble" / "documents" / "gift-cards.md", "rb") as f:
            client.post("/v1/tenants/bramble/documents", headers=ines, files={"file": ("gift-cards.md", f)})
        # 3. invalid files
        cut = (DATA / "larkfield" / "documents" / "warranty-policy.pdf").read_bytes()[:1500]
        r = call("invalid file: a PDF cut during the upload (accepted, then indexed)", "POST",
                 "/v1/tenants/larkfield/documents", grace, files={"file": ("warranty-cut.pdf", cut)})
        drain(app.state.db, app.state.embedder)
        bad_id = r.json()["document"]["document_id"]
        call("invalid file: its status after indexing", "GET", f"/v1/tenants/larkfield/documents/{bad_id}", grace)
        client.delete(f"/v1/tenants/larkfield/documents/{bad_id}", headers=grace)
        call("invalid file: a Word file", "POST", "/v1/tenants/larkfield/documents", grace,
             files={"file": ("returns.docx", b"PK\x03\x04 not a document we read")})
        call("invalid file: 6 MB", "POST", "/v1/tenants/larkfield/documents", grace,
             files={"file": ("big.md", b"# Big\n\n" + b"word " * 1_200_000)})
        # 4. provider timeout
        with FakeProvider("slow", delay=30) as fake:
            app.state.provider = LiveProvider(fake.url, "", timeout_s=2, retries=2)
            call("provider timeout: 2 s timeout, 2 retries", "POST", "/v1/tenants/bramble/answers", ines,
                 json={"question": "How long does delivery to Ontario take?"})
            calls = len(fake.calls)
        out[-1]["provider_calls"] = calls
        drain(app.state.db, app.state.embedder)   # the gift card policy again
    if args.json:
        print(json.dumps(out, indent=1, ensure_ascii=False))
        return 0
    for o in out:
        extra = {k: v for k, v in o.items() if k not in ("case", "status", "seconds") and v not in (None, "")}
        print(f"{o['case']}\n  -> {o['status']} in {o['seconds']} s: {json.dumps(extra, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
