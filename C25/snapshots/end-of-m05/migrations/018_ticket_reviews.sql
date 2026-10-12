-- Agents' reviews: the labels that arrive later (the MLOps course, Module 4).
-- When an agent handles a ticket, they record the team that was right and whether a person
-- had to handle it. The review is compared with the assistant's decision at that moment:
-- these are the delayed labels that measure the assistant's quality.
CREATE TABLE ticket_reviews (
    ticket_id         text        PRIMARY KEY REFERENCES tickets (ticket_id) ON DELETE CASCADE,
    team              text        NOT NULL,
    needs_human       boolean     NOT NULL,
    reviewed_by       text        NOT NULL,
    reviewed_at       timestamptz NOT NULL DEFAULT now(),
    -- the assistant's decision when the review arrived (NULL: it gave no valid answer)
    assistant_team    text,
    assistant_needs_human boolean,
    prompt_version    text,
    release_id        text,
    CONSTRAINT ticket_reviews_team_known CHECK (team IN
        ('billing', 'login', 'shipping', 'account', 'other', 'delivery', 'returns', 'payment', 'warranty'))
);
