"""The ingestion worker: takes uploaded documents from the queue and indexes them.

    python -m doc_assistant.worker        run it as its own process (INGEST_WORKER=off in the API)

By default the API runs it in a background thread (INGEST_WORKER=thread): one process, one copy
of the embedding model. The queue is the documents table itself (the scaling course's pattern):
a document waits with status "uploaded"; the worker claims one with FOR UPDATE SKIP LOCKED, so
two workers never take the same document, and sets "parsing" with a lease. A worker that dies
leaves its lease behind; when the lease ends, another worker takes the document again.

    a file that cannot be parsed   -> failed at once (trying again would fail the same way)
    any other error                -> back to "uploaded", at most MAX_ATTEMPTS attempts in all
Indexing a document twice is safe: its old chunks are deleted in the same transaction.
"""

import logging
import signal
import threading
import time

import psycopg

from .chunk import structure
from .parse import ParseError, parse

logger = logging.getLogger("doc_assistant.worker")
MAX_ATTEMPTS = 3
LEASE = "5 minutes"

CLAIM = f"""UPDATE documents SET status = 'parsing', attempts = attempts + 1, locked_until = now() + interval '{LEASE}'
WHERE document_id = (
    SELECT document_id FROM documents
    WHERE status = 'uploaded' OR (status = 'parsing' AND locked_until < now())
    ORDER BY uploaded_at FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING document_id::text AS document_id, tenant_id, doc_key, version, title, file_name, attempts"""


def claim(db) -> dict | None:
    with db.admin() as conn:   # the queue spans every shop: the owner's rights, on purpose
        return conn.execute(CLAIM).fetchone()


def process(db, doc: dict, embedder) -> str:
    """Index one claimed document. Returns its new status."""
    tenant, doc_id = doc["tenant_id"], doc["document_id"]
    try:
        with db.tenant(tenant) as conn:
            row = conn.execute("SELECT data FROM document_files WHERE tenant_id = %s AND document_id = %s",
                               (tenant, doc_id)).fetchone()
        if row is None:
            return "deleted"
        parsed = parse(doc["file_name"], bytes(row["data"]))
        chunks = structure(parsed, tenant, doc["doc_key"], doc["version"], doc["title"])
        vectors = embedder.embed_passages([c.text for c in chunks])
        with db.tenant(tenant) as conn:
            conn.execute("DELETE FROM chunks WHERE tenant_id = %s AND document_id = %s", (tenant, doc_id))
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO chunks (tenant_id, chunk_id, document_id, position, section, text, pages, embedding)"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    [(tenant, c.chunk_id, doc_id, c.position, c.section, c.text, list(c.pages), v)
                     for c, v in zip(chunks, vectors, strict=True)])
            conn.execute("UPDATE documents SET status = 'indexed', error = NULL, locked_until = NULL, chunk_count = %s,"
                         " embedder = %s, indexed_at = now() WHERE tenant_id = %s AND document_id = %s",
                         (len(chunks), embedder.name, tenant, doc_id))
        return "indexed"
    except ParseError as e:
        _finish(db, tenant, doc_id, "failed", str(e))
        return "failed"
    except psycopg.errors.ForeignKeyViolation:
        return "deleted"   # deleted while it was being indexed: nothing to do
    except Exception as e:  # noqa: BLE001 - any other error: try again later, a bounded number of times
        logger.exception("indexing %s failed (attempt %s)", doc_id, doc["attempts"])
        if doc["attempts"] >= MAX_ATTEMPTS:
            _finish(db, tenant, doc_id, "failed", f"Indexing failed {doc['attempts']} times ({type(e).__name__}).")
            return "failed"
        _finish(db, tenant, doc_id, "uploaded", f"Attempt {doc['attempts']} failed ({type(e).__name__}); "
                                                 "it will be tried again.")
        return "uploaded"


def _finish(db, tenant: str, doc_id: str, status: str, error: str) -> None:
    with db.tenant(tenant) as conn:
        conn.execute("UPDATE documents SET status = %s, error = %s, locked_until = NULL"
                     " WHERE tenant_id = %s AND document_id = %s", (status, error, tenant, doc_id))


def drain(db, embedder) -> dict:
    """Index every waiting document now (scripts and tests). Returns how many ended in each status."""
    counts: dict[str, int] = {}
    while (doc := claim(db)) is not None:
        status = process(db, doc, embedder)
        counts[status] = counts.get(status, 0) + 1
    return counts


def run(db, embedder, stop: threading.Event, poll_s: float = 1.0) -> None:
    while not stop.is_set():
        try:
            doc = claim(db)
        except Exception:  # noqa: BLE001 - the database is down: wait and try again
            logger.warning("the worker cannot reach the database; it tries again in 5 s")
            stop.wait(5)
            continue
        if doc is None:
            stop.wait(poll_s)
            continue
        status = process(db, doc, embedder)
        logger.info("document %s: %s", doc["document_id"], status)


class WorkerThread:
    def __init__(self, db, embedder):
        self.stop = threading.Event()
        self.thread = threading.Thread(target=run, args=(db, embedder, self.stop), name="ingest-worker", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def close(self) -> None:
        self.stop.set()
        self.thread.join(timeout=30)


def main() -> None:
    from .config import settings
    from .db import Database
    from .embed import make_embedder

    s = settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db = Database(s.database_url, s.app_db_role)
    db.open()
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    print("The worker is waiting for documents. Ctrl+C stops it.")
    run(db, make_embedder(s.embedder, s.torch_threads), stop)
    db.close()
    time.sleep(0)


if __name__ == "__main__":
    main()
