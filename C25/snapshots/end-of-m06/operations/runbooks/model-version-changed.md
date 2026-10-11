# Runbook: the provider changed the model

**Alert:** `model-version-changed` (SEV-3). **Owner:** Priya.

## Detection

- Answers name a model version that is not the release manifest's `expected_version`
  (dashboard "Model versions that answered"; `python -m ops rag FILE`).

## Triage

1. Is the new version used for every call or only some? Providers move traffic step by step.
2. Did anything else change at the same time: answers without text, time, tokens, the share
   sent to a person, agents' reviews?

## Mitigation

- If the provider lets you pin a model version, pin the release's version.
- If not: run the release gate's evaluation set against the new version as soon as possible
  (the evaluation course's harness), and watch the reviews more closely (more tickets to
  review for a week).

## Recovery checks

- [ ] Either the answers name the expected version again, or a new release manifest names
      the new version after its evaluation passed the gate.
