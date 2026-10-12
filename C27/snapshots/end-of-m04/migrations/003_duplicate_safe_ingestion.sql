-- Duplicate-safe ingestion (Module 4): the same file uploaded twice by one shop is one document.
-- (Two shops may upload the same file: each gets its own copy.)
ALTER TABLE documents ADD CONSTRAINT documents_same_file_once UNIQUE (tenant_id, sha256);
