-- The capstone's core schema (designed in Module 2, applied from Module 3).
-- Every table that holds a shop's data has tenant_id, and every key that points at another
-- shop's row includes it: a chunk cannot belong to a document of another shop.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tenants (
    tenant_id  text PRIMARY KEY CHECK (tenant_id ~ '^[a-z][a-z0-9-]{1,30}$'),
    name       text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    user_id text PRIMARY KEY,
    name    text NOT NULL,
    email   text NOT NULL
);

CREATE TABLE memberships (
    tenant_id text NOT NULL REFERENCES tenants,
    user_id   text NOT NULL REFERENCES users,
    role      text NOT NULL CHECK (role IN ('owner', 'staff', 'read_only')),
    PRIMARY KEY (tenant_id, user_id)
);

-- One row per uploaded file. The row is also the ingestion job: its status moves
-- uploaded -> parsing -> indexed, or -> failed with an error message.
CREATE TABLE documents (
    document_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      text NOT NULL REFERENCES tenants,
    doc_key        text NOT NULL,
    version        text NOT NULL,
    title          text NOT NULL,
    doc_type       text NOT NULL DEFAULT 'policy',
    language       text NOT NULL DEFAULT 'en',
    access         text NOT NULL DEFAULT 'staff' CHECK (access IN ('public', 'staff')),
    effective_from date NOT NULL,
    effective_to   date,
    file_name      text NOT NULL,
    content_type   text NOT NULL,
    size_bytes     integer NOT NULL CHECK (size_bytes > 0),
    sha256         text NOT NULL,
    status         text NOT NULL DEFAULT 'uploaded'
                   CHECK (status IN ('uploaded', 'parsing', 'indexed', 'failed')),
    error          text,
    attempts       integer NOT NULL DEFAULT 0,
    locked_until   timestamptz,
    chunk_count    integer NOT NULL DEFAULT 0,
    embedder       text,          -- the model that made the vectors; a search uses only its own model's
    uploaded_by    text NOT NULL REFERENCES users,
    uploaded_at    timestamptz NOT NULL DEFAULT now(),
    indexed_at     timestamptz,
    UNIQUE (tenant_id, document_id),
    UNIQUE (tenant_id, doc_key, version),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE INDEX documents_queue ON documents (uploaded_at) WHERE status IN ('uploaded', 'parsing');

CREATE TABLE document_files (
    tenant_id   text NOT NULL,
    document_id uuid NOT NULL,
    data        bytea NOT NULL,
    PRIMARY KEY (tenant_id, document_id),
    FOREIGN KEY (tenant_id, document_id) REFERENCES documents (tenant_id, document_id) ON DELETE CASCADE
);

-- Chunks and their vectors (multilingual-e5-small: 384 numbers). Deleting a document deletes them.
CREATE TABLE chunks (
    tenant_id   text NOT NULL,
    chunk_id    text NOT NULL,
    document_id uuid NOT NULL,
    position    integer NOT NULL,
    section     text NOT NULL DEFAULT '',
    text        text NOT NULL,
    pages       integer[] NOT NULL DEFAULT '{}',
    embedding   vector(384) NOT NULL,
    PRIMARY KEY (tenant_id, chunk_id),
    FOREIGN KEY (tenant_id, document_id) REFERENCES documents (tenant_id, document_id) ON DELETE CASCADE
);
CREATE INDEX chunks_document ON chunks (tenant_id, document_id);

-- Every answer, with its evidence and what it cost.
CREATE TABLE answers (
    answer_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       text NOT NULL REFERENCES tenants,
    user_id         text NOT NULL REFERENCES users,
    question        text NOT NULL,
    as_of           date NOT NULL,
    answerable      boolean NOT NULL,
    answer          text NOT NULL,
    citations       jsonb NOT NULL DEFAULT '[]',
    cited_documents uuid[] NOT NULL DEFAULT '{}',
    checks          jsonb NOT NULL DEFAULT '[]',
    provider        text NOT NULL,
    model           text NOT NULL,
    input_tokens    integer NOT NULL DEFAULT 0,
    output_tokens   integer NOT NULL DEFAULT 0,
    cost_usd        numeric(12, 8) NOT NULL DEFAULT 0,
    latency_ms      integer NOT NULL,
    trace_id        text NOT NULL DEFAULT '',
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX answers_tenant_created ON answers (tenant_id, created_at DESC);
