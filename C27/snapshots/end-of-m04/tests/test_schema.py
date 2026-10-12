"""The core schema (Module 2's design): every row belongs to one shop, and keys keep it so."""

import psycopg
import pytest


@pytest.fixture
def conn(db_url):
    with psycopg.connect(db_url) as c:
        yield c
        c.rollback()


def test_the_core_tables_exist(conn):
    names = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")}
    assert {"tenants", "users", "memberships", "documents", "document_files", "chunks", "answers"} <= names
    assert conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()


def doc(conn, tenant="larkfield", key="test-doc"):
    return conn.execute(
        "INSERT INTO documents (tenant_id, doc_key, version, title, effective_from, file_name, content_type, size_bytes,"
        " sha256, uploaded_by) VALUES (%s, %s, '1', 'T', '2026-01-01', 'x.md', 'text/markdown', 10, %s, 'usr-grace')"
        " RETURNING document_id", (tenant, key, f"sha-{tenant}-{key}")).fetchone()[0]


def test_a_chunk_cannot_point_at_another_shops_document(conn):
    d = doc(conn, "larkfield")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute("INSERT INTO chunks (tenant_id, chunk_id, document_id, position, text, embedding)"
                     " VALUES ('bramble', 'aaaaaaaaaaaa', %s, 0, 'x', %s::vector)", (d, "[" + ",".join(["0"] * 384) + "]"))


def test_the_same_document_key_may_exist_in_two_shops(conn):
    doc(conn, "larkfield", "returns-policy-test")
    doc(conn, "bramble", "returns-policy-test")
    with pytest.raises(psycopg.errors.UniqueViolation):
        doc(conn, "bramble", "returns-policy-test")


@pytest.mark.parametrize("column, value", [("status", "done"), ("access", "secret")])
def test_states_and_access_levels_are_checked(conn, column, value):
    d = doc(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(f"UPDATE documents SET {column} = %s WHERE document_id = %s", (value, d))
