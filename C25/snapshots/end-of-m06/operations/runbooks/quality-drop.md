# Runbook: agents disagree with the assistant

**Alert:** `reviews-disagree` (SEV-3). **Owner:** Priya.

## Detection

- More than 10% of agents' reviews in 30 minutes disagree with the team or the
  needs-a-person decision (the quality SLO is 90%).

## Triage

1. Is it a release? `python -m ops labels FILE --by release`.
2. Did the tickets change? `python -m ops drift FILE --at MINUTE`: language, length, topics.
3. Which kind of ticket? Read 20 disagreeing tickets with the agents.

## Mitigation and change (see the improvement table in docs/improve.md)

- A new kind of ticket the policy does not answer: change the policy text first (Grace), then
  the prompt; add the new tickets to the evaluation set.
- A release: roll back.
- Never retrain or change the prompt only because a drift alert fired: drift is not an error.

## Recovery checks

- [ ] Agreement is above 90% again on at least 139 new reviews (a margin of about 5 points).
