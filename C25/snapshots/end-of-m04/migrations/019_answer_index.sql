-- The retrieval index of the answers (the MLOps course, Module 4).
-- Answers search this index, not the documents table: the index is a copy of the documents,
-- built by python -m scripts.reindex. When a document changes and nobody rebuilds the
-- index, answers quote the old version: a stale index. index_version is the documents
-- fingerprint at the time of the build.
CREATE TABLE answer_index (
    doc_id        text        NOT NULL,
    version       integer     NOT NULL,
    title         text        NOT NULL,
    body          text        NOT NULL,
    access        text        NOT NULL,
    search        tsvector    NOT NULL,
    index_version text        NOT NULL,
    indexed_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (doc_id)
);
CREATE INDEX answer_index_search_idx ON answer_index USING gin (search);

-- Build it once from the current documents, so the answers work after the migration.
INSERT INTO answer_index (doc_id, version, title, body, access, search, index_version)
SELECT doc_id, version, title, body, access,
       to_tsvector('english', title || ' ' || body),
       (SELECT left(md5(string_agg(doc_id || ':' || version || ':' || sha256, ','
                ORDER BY doc_id, version)), 12) FROM documents)
FROM documents WHERE effective_to IS NULL;
