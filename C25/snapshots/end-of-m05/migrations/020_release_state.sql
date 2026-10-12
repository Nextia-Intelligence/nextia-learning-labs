-- Controlled rollouts (the MLOps course, Module 5).
-- Which release does the work: the active release, a canary release for a share of the
-- tickets, and a shadow release that runs beside the active one without changing anything.
-- The worker reads this row every few seconds. Every change is kept in release_events: the
-- timeline of a rollout and of a rollback.
CREATE TABLE release_state (
    id            smallint    PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    active        text        NOT NULL,
    canary        text,
    canary_share  real        NOT NULL DEFAULT 0 CHECK (canary_share >= 0 AND canary_share <= 1),
    shadow        text,
    changed_at    timestamptz NOT NULL DEFAULT now(),
    changed_by    text        NOT NULL,
    reason        text        NOT NULL DEFAULT ''
);

CREATE TABLE release_events (
    event_id      bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    at            timestamptz NOT NULL DEFAULT now(),
    action        text        NOT NULL,
    active        text        NOT NULL,
    canary        text,
    canary_share  real        NOT NULL DEFAULT 0,
    shadow        text,
    changed_by    text        NOT NULL,
    reason        text        NOT NULL DEFAULT '',
    CONSTRAINT release_events_action_known
        CHECK (action IN ('start', 'canary', 'shadow', 'promote', 'rollback', 'stop'))
);

-- A shadow result: the shadow release's triage of a ticket, saved but never used.
ALTER TABLE ai_runs DROP CONSTRAINT ai_runs_task_known;
ALTER TABLE ai_runs ADD CONSTRAINT ai_runs_task_known
    CHECK (task IN ('classify', 'draft_reply', 'embed', 'triage', 'triage_shadow'));
