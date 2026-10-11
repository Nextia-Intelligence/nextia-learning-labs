-- Release IDs on AI results (the MLOps course, Module 2).
-- Every AI result says which release made it: the release manifest
-- operations/releases/<release_id>.toml names the code, prompt, model and data versions.
-- NULL for the results made before, and when the service runs without RELEASE_ID.
ALTER TABLE ai_runs ADD COLUMN release_id text;
CREATE INDEX ai_runs_release_idx ON ai_runs (release_id, created_at);
