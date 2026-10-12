"""Find the passages for a question, inside one shop (the RAG course's search, in PostgreSQL).

Filters, applied BEFORE the top k (so a filtered-out chunk never takes a place):
    the shop          c.tenant_id = the caller's shop (and row-level security, Module 4)
    the access level  a read-only member never gets a staff-only chunk
    the date          the version of a document that is in force on the question's date
    the model         only chunks whose vectors were made by the same embedding model

The search: the question's vector against every chunk's vector (cosine distance, <=>), exact
search: no index is needed for a few thousand chunks. The best TOP_K stay.
"""

from .context import Passage

COLUMNS = """c.chunk_id, c.document_id::text AS document_id, d.doc_key, d.version, d.title, d.doc_type, d.access,
       d.effective_from::text AS effective_from, coalesce(d.effective_to::text, '') AS effective_to,
       c.section, c.text, c.pages"""
FILTERS = """c.tenant_id = %(tenant)s AND d.status = 'indexed' AND d.embedder = %(embedder)s
  AND d.access = ANY(%(access)s)
  AND d.effective_from <= %(as_of)s AND (d.effective_to IS NULL OR d.effective_to >= %(as_of)s)"""
JOIN = "chunks c JOIN documents d ON d.tenant_id = c.tenant_id AND d.document_id = c.document_id"

DENSE = f"""SELECT {COLUMNS}, 1 - (c.embedding <=> %(vector)s) AS score
FROM {JOIN}
WHERE {FILTERS}
ORDER BY c.embedding <=> %(vector)s, c.chunk_id
LIMIT %(k)s"""

def _passages(rows) -> list[Passage]:
    return [Passage(r["chunk_id"], r["document_id"], r["doc_key"], r["version"], r["title"], r["doc_type"],
                    r["access"], r["effective_from"], r["effective_to"], r["section"], r["text"],
                    tuple(r["pages"] or ()), round(float(r["score"]), 4)) for r in rows]


def search(conn, question: str, tenant: str, access: tuple[str, ...], as_of: str, embedder, settings) -> list[Passage]:
    vector = embedder.embed_queries([question])[0]
    params = {"tenant": tenant, "access": list(access), "as_of": as_of, "embedder": embedder.name,
              "vector": vector, "k": settings.top_k}
    return _passages(conn.execute(DENSE, params).fetchall())


def lookup(conn, tenant: str, access: tuple[str, ...], chunk_ids: list[str]) -> dict[str, Passage]:
    """The cited chunks that exist in this shop at the caller's access level. A cited ID of another
    shop, or of a staff-only chunk for a read-only member, is "missing": nothing about it is shown."""
    if not chunk_ids:
        return {}
    rows = conn.execute(f"SELECT {COLUMNS}, 0.0 AS score FROM {JOIN}"
                        " WHERE c.tenant_id = %s AND d.access = ANY(%s) AND c.chunk_id = ANY(%s)",
                        (tenant, list(access), list(chunk_ids))).fetchall()
    return {p.chunk_id: p for p in _passages(rows)}
