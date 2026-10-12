"""The ingestion worker: claims, states, failures with a message, bounded retries."""

from pathlib import Path

from doc_assistant import worker
from tests.conftest import index_all, upload

DATA = Path(__file__).resolve().parent.parent / "data"


def status(client, token, tenant, doc_id):
    return client.get(f"/v1/tenants/{tenant}/documents/{doc_id}", headers=token("usr-ines")).json()["document"]


def test_the_whole_pack_indexes(loaded, token):
    data = loaded.get("/v1/tenants/bramble/documents", headers=token("usr-ines")).json()
    assert data["counts"] == {"indexed": 15} and sum(d["chunk_count"] for d in data["documents"]) == 60
    pdf = next(d for d in data["documents"] if d["doc_key"] == "events-and-room-hire")
    assert pdf["chunk_count"] == 4


def test_a_file_that_cannot_be_parsed_fails_with_a_message(client, token, tmp_path):
    bad = tmp_path / "price-list.pdf"
    bad.write_bytes(b"%PDF-1.7\n1 0 obj << /Type /Catalog >> endobj\nthis file was cut during the upload")
    doc = upload(client, token("usr-ines"), "bramble", bad).json()["document"]
    assert doc["status"] == "uploaded"
    assert index_all(client) == {"failed": 1}
    after = status(client, token, "bramble", doc["document_id"])
    assert after["status"] == "failed" and "not a readable PDF" in after["error"] and after["attempts"] == 1


class BrokenEmbedder:
    name = "hash-384"

    def embed_passages(self, texts):
        raise RuntimeError("the model ran out of memory")


def test_other_errors_are_tried_again_at_most_three_times(client, token):
    doc = upload(client, token("usr-ines"), "bramble", DATA / "bramble" / "documents" / "faq.md").json()["document"]
    db = client.app.state.db
    seen = []
    for _ in range(4):
        claimed = worker.claim(db)
        if claimed is None:
            break
        seen.append(worker.process(db, claimed, BrokenEmbedder()))
    assert seen == ["uploaded", "uploaded", "failed"]
    after = status(client, token, "bramble", doc["document_id"])
    assert after["error"] == "Indexing failed 3 times (RuntimeError)." and after["attempts"] == 3


def test_indexing_twice_keeps_one_copy_of_the_chunks(loaded, token):
    db = loaded.app.state.db
    with db.admin() as conn:
        before = conn.execute("SELECT count(*) AS n FROM chunks").fetchone()["n"]
        conn.execute("UPDATE documents SET status = 'uploaded' WHERE doc_key = 'faq'")
    index_all(loaded)
    with db.admin() as conn:
        assert conn.execute("SELECT count(*) AS n FROM chunks").fetchone()["n"] == before
