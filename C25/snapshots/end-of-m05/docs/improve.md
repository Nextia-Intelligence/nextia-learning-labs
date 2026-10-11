# Retrain or revise: from a symptom to the change that fixes its cause

A symptom says that something is wrong. The change must fit the cause. Find the cause first
(the telemetry, the reviews, the release history), then choose the smallest change that fixes
it, and prove it with the release gate.

| Symptom | Check first | Likely cause | Change |
|---|---|---|---|
| Answers without text after a release | `ops quality --by release`, `ops rollout history` | the new prompt makes the model reason until the token limit | roll back; revise the prompt; gate it on the critical cases |
| Agents correct the team more often, and new kinds of tickets arrive | `ops drift`, `ops labels`, read 20 tickets | the policy does not cover the new topic | change the policy text (Grace), then the prompt; add the tickets to the evaluation set |
| More French tickets, agreement unchanged | `ops drift`, `ops labels` | the inputs changed, the decisions did not | nothing to fix: watch the reviews; drift is not an error |
| Answers quote an old price | `ops rag`, `scripts.reindex --check` | the index is older than the documents | rebuild the index; rebuild it when documents change |
| Answers change after a date, no release | `ops rag` (model versions) | the provider changed the model | pin the version, or evaluate the new one through the gate |
| Many tickets wait, no wrong answers | `ops incident`, the circuit breaker | the provider is down or slow | wait with the breaker; tell customers; do not add retries |
| Cost per ticket goes up | `ops quality` (tokens out) | longer reasoning or longer replies | revise the prompt or the token limit; gate on cost |

Retraining a model (or fine-tuning one) is the most expensive change, and here the model
belongs to the provider. Choose it only when the evaluation shows the model itself cannot do
the task with any prompt and policy you tried, and you have labelled data to train on.
