# Runbook: answers quote old documents

**Alert:** `old-sources` (SEV-3). **Owner:** Tomás (the retrieval index).

## Detection

- Answers whose sources are not the current version of their documents (`stale_sources` > 0
  in the `answer.served` events; "Answers with old sources" on the AI quality dashboard).
- `python -m scripts.reindex --check` says the index is OLDER than the documents.

## Triage

1. Which documents changed? Compare the versions: `python -m ops rag FILE`.
2. Does the change matter to customers (a price, a time, a rule)? Ask Grace.

## Mitigation

- Rebuild the index: `python -m scripts.reindex`. It takes seconds for the shop's documents.
- The answers cache keys contain the index version, so old answers are not reused.

## Prevention

- Rebuild the index in the same step that publishes a document (the document workflow, not
  a person's memory).

## Recovery checks

- [ ] `python -m scripts.reindex --check` says "up to date".
- [ ] No new answer with old sources in the last 10 minutes.
