"""Permission enforcement: who may do what, in which shop. The matrix is people x shops x actions."""

import pytest

from doc_assistant.pipeline import Deps, ask
from scripts.common import as_member

# (user, shop) -> expected status of: list documents, ask, upload
MATRIX = [
    ("usr-grace", "larkfield", 200, 200, 202),    # owner
    ("usr-sam", "larkfield", 200, 200, 202),      # staff
    ("usr-omar", "larkfield", 200, 200, 403),     # read-only: asks, cannot upload
    ("usr-camille", "larkfield", 200, 200, 202),  # staff at Larkfield ...
    ("usr-camille", "bramble", 200, 200, 403),    # ... read-only at Bramble Books
    ("usr-ines", "larkfield", 404, 404, 404),     # owner of the OTHER shop: Larkfield does not exist for her
    ("usr-tomas", "larkfield", 404, 404, 404),    # signed in, member of nothing
    ("usr-sam", "acme", 404, 404, 404),           # a shop that does not exist: the same answer
]


@pytest.mark.parametrize("user, shop, list_status, ask_status, upload_status", MATRIX)
def test_access_matrix(client, token, tmp_path, user, shop, list_status, ask_status, upload_status):
    h = token(user)
    assert client.get(f"/v1/tenants/{shop}/documents", headers=h).status_code == list_status
    assert client.post(f"/v1/tenants/{shop}/answers", json={"question": "Hello?"}, headers=h).status_code == ask_status
    f = tmp_path / "note.md"
    f.write_text(f"# Note\n\n## Text\n\nA note from {user}.\n")
    with open(f, "rb") as fh:
        r = client.post(f"/v1/tenants/{shop}/documents", files={"file": ("note.md", fh)}, headers=h)
    assert r.status_code == upload_status


def test_no_identity_is_401_and_an_outsider_cannot_tell_which_shops_exist(client, token):
    assert client.get("/v1/tenants/larkfield/documents").status_code == 401
    real = client.get("/v1/tenants/larkfield/documents", headers=token("usr-tomas")).json()
    fake = client.get("/v1/tenants/acme/documents", headers=token("usr-tomas")).json()
    assert {k: v for k, v in real.items() if k != "request_id"} == {k: v for k, v in fake.items() if k != "request_id"}


def test_another_shops_document_id_is_not_found(loaded, token):
    docs = loaded.get("/v1/tenants/larkfield/documents", headers=token("usr-sam")).json()["documents"]
    larkfield_doc = docs[0]["document_id"]
    r = loaded.get(f"/v1/tenants/bramble/documents/{larkfield_doc}", headers=token("usr-ines"))
    assert r.status_code == 404
    r = loaded.delete(f"/v1/tenants/bramble/documents/{larkfield_doc}", headers=token("usr-ines"))
    assert r.status_code == 404


def test_a_read_only_member_never_gets_a_staff_only_passage(loaded):
    st = loaded.app.state
    d = Deps(st.db, st.settings, st.embedder, st.provider, st.reranker)
    for user in ("usr-omar",):
        result = ask(d, as_member(d, user, "larkfield"), "What is the staff discount?")
        assert result.passages and all(p["access"] == "public" for p in result.passages)
    staff = ask(d, as_member(d, "usr-sam", "larkfield"), "What is the staff discount?")
    assert any(p["access"] == "staff" for p in staff.passages)


def test_row_level_security_hides_other_shops_even_without_a_filter(loaded):
    db = loaded.app.state.db
    with db.tenant("bramble") as conn:
        shops = {r["tenant_id"] for r in conn.execute("SELECT DISTINCT tenant_id FROM chunks").fetchall()}
        assert shops == {"bramble"}   # the query has no WHERE tenant_id: the policy adds it
        with pytest.raises(Exception, match="row-level security"):
            conn.execute("INSERT INTO answers (tenant_id, user_id, question, as_of, answerable, answer, provider,"
                         " model, latency_ms) VALUES ('larkfield', 'usr-ines', 'x', '2026-10-11', false, 'x', 'x', 'x', 1)")
    with db.admin() as conn:   # the owner (a superuser in Compose) is not limited: why db.tenant() switches role
        assert len(conn.execute("SELECT DISTINCT tenant_id FROM chunks").fetchall()) == 2


def test_without_a_tenant_setting_the_app_role_sees_nothing(loaded):
    with loaded.app.state.db.admin() as conn:
        conn.execute("SET LOCAL ROLE assistant_app")
        assert conn.execute("SELECT count(*) AS n FROM documents").fetchone()["n"] == 0
