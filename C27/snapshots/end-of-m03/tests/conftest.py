"""Shared test setup. Tests that need PostgreSQL use TEST_DATABASE_URL (see .env.example): the
session makes that database new, applies every migration and loads the identity data. They never
touch DATABASE_URL. Without TEST_DATABASE_URL they are skipped, and the others still run.

The tests use the stand-ins: the hash embedder (no model download) and the mock provider (no
model). Nobody signs in yet (Module 4 adds it): every request acts as the practice user, so the
`token` fixture gives no header. The tests already pass it, so they keep working in Module 4.
"""

import os
from dataclasses import replace
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from doc_assistant.config import Settings, load_env_file

ROOT = Path(__file__).resolve().parent.parent
load_env_file()


def test_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", "")


@pytest.fixture(scope="session")
def db_url():
    url = test_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set: the database tests are skipped")
    info = psycopg.conninfo.conninfo_to_dict(url)
    name = info["dbname"]
    admin = psycopg.conninfo.make_conninfo(url, dbname="postgres")
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    from doc_assistant.migrate import migrate

    migrate(url, quiet=True)
    from scripts.load_pack import load_identity

    with psycopg.connect(url) as conn:
        load_identity(conn)
    return url


@pytest.fixture(scope="session")
def settings(db_url) -> Settings:
    return Settings(database_url=db_url, answer_provider="mock", embedder="hash", ingest_worker="off",
                    auth_mode="dev", trace_file="", today="2026-10-11")


@pytest.fixture(scope="session")
def token():
    def make(user: str, **extra) -> dict:
        return {}   # Module 3: no sign-in yet

    return make


def wipe(url: str) -> None:
    with psycopg.connect(url) as conn:
        conn.execute("TRUNCATE answers, chunks, document_files, documents")


@pytest.fixture
def make_client(settings):
    """A TestClient of a new app with these settings (the database is emptied first)."""
    from fastapi.testclient import TestClient

    from doc_assistant.main import create_app

    clients = []

    def make(**changes):
        wipe(settings.database_url)
        app = create_app(replace(settings, **changes), start_worker=False)
        client = TestClient(app)
        client.__enter__()
        clients.append(client)
        return client

    yield make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def client(make_client):
    return make_client()


def upload(client, headers, tenant: str, path: Path, **form):
    with open(path, "rb") as f:
        return client.post(f"/v1/tenants/{tenant}/documents", headers=headers, files={"file": (path.name, f)},
                           data=form)


def index_all(client) -> dict:
    from doc_assistant.worker import drain

    return drain(client.app.state.db, client.app.state.embedder)


@pytest.fixture
def loaded(client, token):
    """Both shops' data packs, uploaded through the API by their owners and indexed."""
    for tenant, owner in (("larkfield", "usr-grace"), ("bramble", "usr-ines")):
        for p in sorted((ROOT / "data" / tenant / "documents").iterdir()):
            r = upload(client, token(owner), tenant, p)
            assert r.status_code == 202, r.text
    counts = index_all(client)
    assert counts == {"indexed": 51}, counts
    return client
