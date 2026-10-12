-- Usage per shop and day, for the limits of Module 6. It is not deleted with an answer or a
-- document, so deleting material does not reset a shop's usage.
CREATE TABLE usage_days (
    tenant_id text NOT NULL REFERENCES tenants,
    day       date NOT NULL,
    questions integer NOT NULL DEFAULT 0,
    cost_usd  numeric(12, 8) NOT NULL DEFAULT 0,
    PRIMARY KEY (tenant_id, day)
);
GRANT SELECT, INSERT, UPDATE ON usage_days TO assistant_app;
ALTER TABLE usage_days ENABLE ROW LEVEL SECURITY;
CREATE POLICY one_tenant ON usage_days
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
