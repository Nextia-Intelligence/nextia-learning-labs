"""Isolation checks: try, on purpose, to reach one shop's data from the other (Module 5).

    python -m scripts.isolation            every check; prints the probes and the leaks (must be 0)
    python -m scripts.isolation --json

Three layers, each tried for real against your own practice data:
1. Search:   every question of the bank, asked by a member of the OTHER shop. A leak is any
             passage of the first shop in the results.
2. API:      every route, called by a member of shop B with shop A's IDs (documents, chunks,
             answers), through shop A's path and through B's own path. A leak is any answer
             other than 404 not_found, or any body that contains A's data.
3. Database: inside shop B's transaction (row-level security), queries WITHOUT a tenant filter.
             A leak is any row of shop A.
Plus the access level: every staff-only question, asked by a read-only member; a leak is any
staff-only passage. The API runs in this process with practice tokens (no server needed).
"""

import argparse
import json
from dataclasses import replace

from fastapi.testclient import TestClient

from doc_assistant import retrieve
from doc_assistant.config import settings as load_settings
from doc_assistant.main import create_app

from . import holdout
from .common import READ_ONLY, STAFF, as_member, open_deps
from .evaluate import EVAL
from .practice import practice_tokens

OTHER = {"larkfield": "bramble", "bramble": "larkfield"}


def search_checks(deps, questions) -> dict:
    probes = leaks = 0
    with deps.db.admin() as conn:
        owner = {r["document_id"]: r["tenant_id"] for r in
                 conn.execute("SELECT document_id::text AS document_id, tenant_id FROM documents").fetchall()}
    for q in questions:
        other = OTHER[q["tenant"]]
        who = as_member(deps, STAFF[other], other)
        with deps.db.tenant(other) as conn:
            found = retrieve.search(conn, q["question"], other, who.access_levels, q["as_of"], deps.embedder,
                                    deps.settings, deps.reranker)
        probes += 1
        leaks += sum(owner.get(p.document_id) != other for p in found)
    staff_q = [q for q in questions if q["kind"] == "staff-only"]
    access_leaks = 0
    for q in staff_q:
        who = as_member(deps, READ_ONLY[q["tenant"]], q["tenant"])
        with deps.db.tenant(q["tenant"]) as conn:
            found = retrieve.search(conn, q["question"], q["tenant"], who.access_levels, q["as_of"], deps.embedder,
                                    deps.settings, deps.reranker)
        access_leaks += sum(p.access != "public" for p in found)
    return {"cross_shop_searches": probes, "cross_shop_passages": leaks,
            "read_only_searches": len(staff_q), "staff_only_passages_shown": access_leaks}


def api_checks(settings) -> dict:
    token, validator = practice_tokens()
    app = create_app(replace(settings, trace_file=""), start_worker=False)
    probes, leaks, statuses = 0, [], {}
    with TestClient(app) as client:
        app.state.validator = validator
        ids = {}
        with app.state.db.admin() as conn:
            for t in OTHER:
                ids[t] = {
                    "documents": [r["id"] for r in conn.execute(
                        "SELECT document_id::text AS id FROM documents WHERE tenant_id = %s", (t,)).fetchall()],
                    "chunks": [r["id"] for r in conn.execute(
                        "SELECT chunk_id AS id FROM chunks WHERE tenant_id = %s LIMIT 20", (t,)).fetchall()],
                    "answers": [r["id"] for r in conn.execute(
                        "SELECT answer_id::text AS id FROM answers WHERE tenant_id = %s LIMIT 20", (t,)).fetchall()],
                }
        for victim, attacker in OTHER.items():
            h = token(STAFF[attacker])
            calls = [("GET", f"/v1/tenants/{victim}/documents"), ("GET", f"/v1/tenants/{victim}/answers"),
                     ("GET", f"/v1/tenants/{victim}/usage"), ("POST", f"/v1/tenants/{victim}/answers")]
            for kind in ("documents", "chunks", "answers"):
                for i in ids[victim][kind]:
                    for shop in (victim, attacker):     # through the victim's path and through one's own
                        calls.append(("GET", f"/v1/tenants/{shop}/{kind}/{i}"))
                        if kind == "documents":
                            calls.append(("DELETE", f"/v1/tenants/{shop}/{kind}/{i}"))
            for method, path in calls:
                if method == "POST":
                    r = client.post(path, json={"question": "What are your policies?"}, headers=h)
                else:
                    r = client.request(method, path, headers=h)
                probes += 1
                statuses[r.status_code] = statuses.get(r.status_code, 0) + 1
                body = r.text
                leaked = r.status_code != 404 or any(i in body for kind in ids[victim].values() for i in kind)
                if leaked:
                    leaks.append(f"{method} {path} -> {r.status_code}")
    return {"api_probes": probes, "api_leaks": len(leaks), "api_statuses": statuses, "api_leak_examples": leaks[:5]}


def database_checks(deps) -> dict:
    probes = leaks = 0
    for shop in OTHER:
        with deps.db.tenant(shop) as conn:
            for table in ("documents", "document_files", "chunks", "answers"):
                probes += 1
                rows = conn.execute(f"SELECT tenant_id, count(*) AS n FROM {table} GROUP BY tenant_id").fetchall()
                leaks += sum(r["n"] for r in rows if r["tenant_id"] != shop)
    return {"database_probes": probes, "database_rows_of_other_shop": leaks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.isolation")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    s = load_settings()
    deps = open_deps(s)
    questions = holdout.load(EVAL / "questions.jsonl")
    out = {**search_checks(deps, questions), **database_checks(deps)}
    deps.db.close()
    out.update(api_checks(s))
    total = out["cross_shop_searches"] + out["read_only_searches"] + out["database_probes"] + out["api_probes"]
    leaks = (out["cross_shop_passages"] + out["staff_only_passages_shown"] + out["database_rows_of_other_shop"]
             + out["api_leaks"])
    out["probes"], out["leaks"] = total, leaks
    if args.json:
        print(json.dumps(out, indent=1))
    else:
        print(f"Search: {out['cross_shop_searches']} questions asked in the other shop -> "
              f"{out['cross_shop_passages']} passages of the first shop")
        print(f"Access: {out['read_only_searches']} staff-only questions asked by read-only members -> "
              f"{out['staff_only_passages_shown']} staff-only passages")
        print(f"API: {out['api_probes']} requests with the other shop's IDs -> statuses {out['api_statuses']}, "
              f"{out['api_leaks']} leaks")
        print(f"Database: {out['database_probes']} unfiltered queries under row-level security -> "
              f"{out['database_rows_of_other_shop']} rows of the other shop")
        print(f"Isolation checks: {total} probes, {leaks} leaks.")
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
