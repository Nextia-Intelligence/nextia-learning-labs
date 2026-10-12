"""Find the passages for a question, inside one shop (the RAG course's search, in PostgreSQL).

Filters, applied BEFORE the top k (so a filtered-out chunk never takes a place):
    the shop          c.tenant_id = the caller's shop (and row-level security, Module 4)
    the access level  a read-only member never gets a staff-only chunk
    the date          the version of a document that is in force on the question's date
    the model         only chunks whose vectors were made by the same embedding model

Modes (RETRIEVAL_MODE):
    dense          the question's vector against every chunk's vector (cosine distance, <=>),
                   exact search: no index is needed for a few thousand chunks (Module 3)
    hybrid         the best CANDIDATES chunks by vector and the best by keywords (PostgreSQL full
                   text, migration 004), merged with reciprocal rank fusion (Module 5)
    dense_rerank   the best CANDIDATES by vector, reread by the cross-encoder (Module 5)
    hybrid_rerank  hybrid's candidates, reread by the cross-encoder (Module 5)
Every mode keeps the best TOP_K.
"""

import re

from .cite import STOP
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

# Each word of the question (without small common words), joined by OR: a chunk with more (and
# rarer) words ranks higher. plainto_tsquery splits a code the way the index does: PW-2200 -> pw-2200.
KEYWORD = f"""SELECT {COLUMNS}, ts_rank_cd(c.words, kw.q) AS score
FROM {JOIN}
CROSS JOIN (SELECT string_agg('(' || plainto_tsquery('simple', w)::text || ')', ' | ')::tsquery AS q
            FROM unnest(%(words)s::text[]) AS w WHERE plainto_tsquery('simple', w)::text <> '') AS kw
WHERE {FILTERS} AND c.words @@ kw.q
ORDER BY score DESC, c.chunk_id
LIMIT %(k)s"""


def keywords(question: str) -> list[str]:
    return [w for w in dict.fromkeys(re.findall(r"[\w][\w-]*", question.lower())) if w not in STOP and len(w) > 1]


def _passages(rows) -> list[Passage]:
    return [Passage(r["chunk_id"], r["document_id"], r["doc_key"], r["version"], r["title"], r["doc_type"],
                    r["access"], r["effective_from"], r["effective_to"], r["section"], r["text"],
                    tuple(r["pages"] or ()), round(float(r["score"]), 4)) for r in rows]


def rrf(*ranked: list[Passage], k: int = 60) -> list[Passage]:
    """Reciprocal rank fusion: score = sum of 1 / (60 + rank) over the lists that contain a chunk."""
    scores: dict[str, float] = {}
    first: dict[str, Passage] = {}
    for results in ranked:
        for rank, p in enumerate(results, 1):
            scores[p.chunk_id] = scores.get(p.chunk_id, 0.0) + 1 / (k + rank)
            first.setdefault(p.chunk_id, p)
    return [first[c] for c in sorted(scores, key=lambda c: (-scores[c], c))]


MODES = ("dense", "hybrid", "dense_rerank", "hybrid_rerank")


def search(conn, question: str, tenant: str, access: tuple[str, ...], as_of: str, embedder, settings,
           reranker=None, mode: str | None = None) -> list[Passage]:
    mode = mode or settings.retrieval_mode
    if mode not in MODES:
        raise ValueError(f"Unknown RETRIEVAL_MODE {mode!r}: use one of {', '.join(MODES)}.")
    vector = embedder.embed_queries([question])[0]
    params = {"tenant": tenant, "access": list(access), "as_of": as_of, "embedder": embedder.name,
              "vector": vector, "words": keywords(question)}
    if mode == "dense":
        return _passages(conn.execute(DENSE, {**params, "k": settings.top_k}).fetchall())
    candidates = _passages(conn.execute(DENSE, {**params, "k": settings.candidates}).fetchall())
    if mode in ("hybrid", "hybrid_rerank"):
        words = _passages(conn.execute(KEYWORD, {**params, "k": settings.candidates}).fetchall())
        candidates = rrf(candidates, words)[: settings.candidates]
    if mode == "hybrid":
        return candidates[: settings.top_k]
    scores = reranker.scores(question, [p.text for p in candidates])
    order = sorted(range(len(candidates)), key=lambda i: (-scores[i], candidates[i].chunk_id))
    return [_replace_score(candidates[i], scores[i]) for i in order[: settings.top_k]]


def _replace_score(p: Passage, score: float) -> Passage:
    from dataclasses import replace

    return replace(p, score=round(float(score), 4))


def lookup(conn, tenant: str, access: tuple[str, ...], chunk_ids: list[str]) -> dict[str, Passage]:
    """The cited chunks that exist in this shop at the caller's access level. A cited ID of another
    shop, or of a staff-only chunk for a read-only member, is "missing": nothing about it is shown."""
    if not chunk_ids:
        return {}
    rows = conn.execute(f"SELECT {COLUMNS}, 0.0 AS score FROM {JOIN}"
                        " WHERE c.tenant_id = %s AND d.access = ANY(%s) AND c.chunk_id = ANY(%s)",
                        (tenant, list(access), list(chunk_ids))).fetchall()
    return {p.chunk_id: p for p in _passages(rows)}
