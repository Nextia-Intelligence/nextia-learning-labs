"""Shared test setup. Tests that need PostgreSQL use TEST_DATABASE_URL (see .env.example): the
session makes that database new, applies every migration and loads the identity data. They never
touch DATABASE_URL. Without TEST_DATABASE_URL they are skipped, and the others still run.

The tests use the stand-ins: the hash embedder and the word-overlap reranker (no model
download), the mock provider (no model), and tokens signed by a practice provider made in a
temporary folder (no identity server).
"""

import os
from dataclasses import replace
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from doc_assistant.config import Settings, load_env_file

ROOT = Path(__file__).resolve().parent.parent
ISSUER = "http://localhost:8400"
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
                    auth_mode="oidc", session_secret="test-session-secret", oidc_client_secret="test-client-secret",
                    session_cookie_secure=False, trace_file="", today="2026-10-11")


@pytest.fixture(scope="session")
def idp_store(tmp_path_factory):
    from idp.store import Store

    store = Store(tmp_path_factory.mktemp("idp"))
    store.init()
    return store


@pytest.fixture(scope="session")
def validator(idp_store):
    from doc_assistant.auth import ProviderConfig, TokenValidator

    def fetch(url: str) -> dict:
        if url.endswith("/.well-known/openid-configuration"):
            return {"issuer": ISSUER, "jwks_uri": f"{ISSUER}/jwks.json", "token_endpoint": f"{ISSUER}/token",
                    "authorization_endpoint": f"{ISSUER}/authorize"}
        return idp_store.jwks()

    return TokenValidator(ProviderConfig(ISSUER, fetch=fetch), "doc-assistant")


@pytest.fixture(scope="session")
def token(idp_store):
    from idp.tokens import Signer

    signer = Signer(idp_store, ISSUER)

    def make(user: str, **extra) -> dict:
        return {"Authorization": f"Bearer {signer.access_token(user, 'tests', 'documents:read documents:write', **extra)}"}

    return make


def wipe(url: str) -> None:
    with psycopg.connect(url) as conn:
        conn.execute("TRUNCATE answers, chunks, document_files, documents")
        if conn.execute("SELECT to_regclass('usage_days') IS NOT NULL").fetchone()[0]:
            conn.execute("TRUNCATE usage_days")


@pytest.fixture
def make_client(settings, validator):
    """A TestClient of a new app with these settings (the database is emptied first)."""
    from fastapi.testclient import TestClient

    from doc_assistant.main import create_app

    clients = []

    def make(**changes):
        wipe(settings.database_url)
        app = create_app(replace(settings, **changes), start_worker=False)
        client = TestClient(app)
        client.__enter__()
        app.state.validator = validator
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
