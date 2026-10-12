"""Shared test setup. Tests that need PostgreSQL use TEST_DATABASE_URL (see .env.example): the
session makes that database new, applies every migration and loads the people and shops of the
data pack. They never touch DATABASE_URL. Without TEST_DATABASE_URL they are skipped, and the
others still run.
"""

import csv
import os
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from doc_assistant.config import load_env_file

ROOT = Path(__file__).resolve().parent.parent
load_env_file()


def rows(name: str) -> list[dict]:
    with open(ROOT / "data" / "identity" / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="session")
def db_url():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set: the database tests are skipped")
    name = psycopg.conninfo.conninfo_to_dict(url)["dbname"]
    admin = psycopg.conninfo.make_conninfo(url, dbname="postgres")
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    from doc_assistant.migrate import migrate

    migrate(url, quiet=True)
    with psycopg.connect(url) as conn:
        for t in rows("tenants.csv"):
            conn.execute("INSERT INTO tenants (tenant_id, name) VALUES (%s, %s)", (t["tenant_id"], t["name"]))
        for u in rows("users.csv"):
            conn.execute("INSERT INTO users (user_id, name, email) VALUES (%s, %s, %s)",
                         (u["user_id"], u["name"], u["email"]))
        for m in rows("memberships.csv"):
            conn.execute("INSERT INTO memberships (tenant_id, user_id, role) VALUES (%s, %s, %s)",
                         (m["tenant_id"], m["user_id"], m["role"]))
    return url
