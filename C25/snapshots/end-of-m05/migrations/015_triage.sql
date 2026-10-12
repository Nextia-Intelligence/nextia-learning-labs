-- The help desk's assistant (the MLOps course, Module 1).
-- One triage request per ticket replaces classify and draft_reply: it chooses the team,
-- decides if a person must handle the ticket, and drafts the reply. The old rows stay.
ALTER TABLE ai_runs DROP CONSTRAINT ai_runs_task_known;
ALTER TABLE ai_runs ADD CONSTRAINT ai_runs_task_known
    CHECK (task IN ('classify', 'draft_reply', 'embed', 'triage'));

-- Why the model stopped: "stop" (it finished) or "length" (it used all its tokens: often no
-- text at all). NULL for the rows made before this migration and for embeddings.
ALTER TABLE ai_runs ADD COLUMN finish_reason text;

-- The assistant's teams. The tickets made before keep their old team names.
ALTER TABLE tickets DROP CONSTRAINT tickets_team_known;
ALTER TABLE tickets ADD CONSTRAINT tickets_team_known CHECK (team IN
    ('billing', 'login', 'shipping', 'account', 'other', 'delivery', 'returns', 'payment', 'warranty'));

-- The assistant's decision: true = a person must handle the ticket (Grace's rules H1 to H5).
-- NULL = not decided yet, or the assistant gave no valid answer.
ALTER TABLE tickets ADD COLUMN needs_human boolean;
