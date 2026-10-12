"""Load the data pack: the shops, the people and their memberships, then every document,
uploaded and indexed by the same code as the API's upload and the worker.

    python -m scripts.load_pack              (applies the migrations first)
    python -m scripts.load_pack --reset      delete every shop's data first, then load
    python -m scripts.load_pack --tenant bramble

Each shop's documents are uploaded by its owner (Grace for Larkfield, Ines for Bramble Books).
Loading twice is safe: a file that is already there is reported as a duplicate, not added again.
"""

import argparse
import csv
import time
from pathlib import Path

from doc_assistant.config import settings as load_settings
from doc_assistant.errors import ApiError
from doc_assistant.ingest import create_document
from doc_assistant.migrate import migrate
from doc_assistant.worker import drain

from .common import open_deps

DATA = Path(__file__).resolve().parent.parent / "data"
OWNERS = {"larkfield": "usr-grace", "bramble": "usr-ines"}


def rows(name: str) -> list[dict]:
    with open(DATA / "identity" / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_identity(conn) -> str:
    tenants, users, members = rows("tenants.csv"), rows("users.csv"), rows("memberships.csv")
    for t in tenants:
        conn.execute("INSERT INTO tenants (tenant_id, name) VALUES (%s, %s) ON CONFLICT (tenant_id) DO UPDATE"
                     " SET name = excluded.name", (t["tenant_id"], t["name"]))
    for u in users:
        conn.execute("INSERT INTO users (user_id, name, email) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE"
                     " SET name = excluded.name, email = excluded.email", (u["user_id"], u["name"], u["email"]))
    for m in members:
        conn.execute("INSERT INTO memberships (tenant_id, user_id, role) VALUES (%s, %s, %s)"
                     " ON CONFLICT (tenant_id, user_id) DO UPDATE SET role = excluded.role",
                     (m["tenant_id"], m["user_id"], m["role"]))
    return f"{len(tenants)} shops, {len(users)} people, {len(members)} memberships"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.load_pack")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--tenant", choices=["all", *OWNERS], default="all")
    args = parser.parse_args(argv)
    s = load_settings()
    migrate(s.database_url, quiet=True)
    deps = open_deps(s)
    with deps.db.admin() as conn:
        if args.reset:
            conn.execute("TRUNCATE answers, chunks, document_files, documents, memberships, users, tenants CASCADE")
            if conn.execute("SELECT to_regclass('usage_days') IS NOT NULL AS x").fetchone()["x"]:
                conn.execute("TRUNCATE usage_days")
            print("Deleted every shop's data.")
        print(f"Identity: {load_identity(conn)}")
    for tenant in (OWNERS if args.tenant == "all" else [args.tenant]):
        added = same = 0
        with open(DATA / tenant / "inventory.csv", encoding="utf-8", newline="") as f:
            inventory = list(csv.DictReader(f))
        with deps.db.tenant(tenant) as conn:
            for row in inventory:
                path = DATA / tenant / row["file"]
                try:
                    _, duplicate = create_document(conn, tenant, OWNERS[tenant], path.name, "", path.read_bytes(), {}, s)
                except ApiError as e:
                    if e.status != 409:
                        raise
                    duplicate = True   # this version of this document is already there
                same += duplicate
                added += not duplicate
        print(f"{tenant}: {added} documents uploaded, {same} already there")
    start = time.monotonic()
    print(f"Indexing with {deps.embedder.name} ...")
    counts = drain(deps.db, deps.embedder)
    with deps.db.admin() as conn:
        rows_ = conn.execute("SELECT tenant_id, count(*) AS docs, sum(chunk_count) AS chunks,"
                             " count(*) FILTER (WHERE status = 'failed') AS failed FROM documents"
                             " GROUP BY tenant_id ORDER BY tenant_id").fetchall()
    print(f"Indexed {counts.get('indexed', 0)} documents in {time.monotonic() - start:.1f} s"
          f" (failed {counts.get('failed', 0)}).")
    for r in rows_:
        print(f"  {r['tenant_id']}: {r['docs']} documents, {r['chunks']} passages, {r['failed']} failed")
    deps.db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
