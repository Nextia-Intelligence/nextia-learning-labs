-- Row-level security: a second lock behind the "tenant_id = ..." in every query (Module 4).
-- The API runs each shop's transaction as the role assistant_app with app.tenant_id set
-- (doc_assistant/db.py). A query that forgets its tenant filter then still sees one shop only.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'assistant_app') THEN
        CREATE ROLE assistant_app NOLOGIN;
    END IF;
END
$$;
-- A managed database's administrator is not a superuser: it must be a member to switch to the role.
GRANT assistant_app TO CURRENT_USER;

GRANT USAGE ON SCHEMA public TO assistant_app;
GRANT SELECT ON tenants, users, memberships TO assistant_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON documents, document_files, chunks, answers TO assistant_app;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE answers ENABLE ROW LEVEL SECURITY;

-- current_setting(..., true) is NULL when app.tenant_id is not set: then no row matches.
CREATE POLICY one_tenant ON documents
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
CREATE POLICY one_tenant ON document_files
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
CREATE POLICY one_tenant ON chunks
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
CREATE POLICY one_tenant ON answers
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
