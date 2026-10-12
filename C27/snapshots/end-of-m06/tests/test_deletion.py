"""User review and cleanup: evidence behind each citation, and deletion that removes everything."""

from doc_assistant.pipeline import Deps, ask
from scripts.common import as_member


def test_a_citation_opens_its_evidence(loaded, token):
    a = loaded.post("/v1/tenants/bramble/answers", json={"question": "How long is a gift card valid?"},
                    headers=token("usr-ines")).json()["answer"]
    cid = a["claims"][0]["citations"][0]["chunk_id"]
    chunk = loaded.get(f"/v1/tenants/bramble/chunks/{cid}", headers=token("usr-ines")).json()["chunk"]
    assert chunk["doc_key"] == "gift-cards" and chunk["text"].startswith("Gift cards")
    assert loaded.get(f"/v1/tenants/larkfield/chunks/{cid}", headers=token("usr-sam")).status_code == 404


def test_deleting_a_document_removes_its_file_chunks_vectors_and_answers(loaded, token):
    h = token("usr-ines")
    a = loaded.post("/v1/tenants/bramble/answers", json={"question": "How long is a gift card valid?"},
                    headers=h).json()["answer"]
    doc_id = a["claims"][0]["citations"][0]["document_id"]
    r = loaded.delete(f"/v1/tenants/bramble/documents/{doc_id}", headers=h)
    assert r.status_code == 200 and r.json()["deleted"]["chunks"] == 4 and r.json()["deleted"]["answers"] == 1
    with loaded.app.state.db.admin() as conn:
        for table in ("documents", "document_files", "chunks", "answers"):
            n = conn.execute(f"SELECT count(*) AS n FROM {table} WHERE tenant_id = 'bramble' AND "
                             + ("document_id = %s" if table != "answers" else "%s = ANY(cited_documents)"),
                             (doc_id,)).fetchone()["n"]
            assert n == 0, table
    st = loaded.app.state
    d = Deps(st.db, st.settings, st.embedder, st.provider, st.reranker)
    again = ask(d, as_member(d, "usr-ines", "bramble"), "How long is a gift card valid?")
    assert "gift-cards" not in {p["doc_key"] for p in again.passages}
    assert loaded.get(f"/v1/tenants/bramble/documents/{doc_id}", headers=h).status_code == 404


def test_a_read_only_member_cannot_delete(loaded, token):
    docs = loaded.get("/v1/tenants/bramble/documents", headers=token("usr-camille")).json()["documents"]
    r = loaded.delete(f"/v1/tenants/bramble/documents/{docs[0]['document_id']}", headers=token("usr-camille"))
    assert r.status_code == 403 and r.json()["code"] == "forbidden"
