# Checking a model judge before trusting it

Recorded (real model). 100 replies of the real assistant (`recordings/judge-set.jsonl`): all 32 replies that the course author labelled as failing in the 300 recorded runs, and 68 passing ones. Two model judges scored each reply 1 to 4 with the same rubric, the policy sections the assistant had, and its tool calls (names and results ok / not found). A score of 3 or 4 counts as pass. Files: `recordings/judge-chat-small.jsonl`, `judge-chat-strong.jsonl`, `judge-summary.json`.

| | chat-small judge | chat-strong judge |
|---|---|---|
| Agreement with the author's labels | 82 of 100 | 74 of 100 |
| Cohen's kappa (agreement beyond chance) | 0.61 | 0.49 |
| Author's failures that the judge also failed | 26 of 32 | 29 of 32 |
| Author's passes that the judge failed (false alarms) | 12 of 68 | 23 of 68 |

## What the judges missed

- Both judges passed the three replies in which the assistant **looked up an order number that the customer never gave** (`LK-000000`, `LK-1001`): the tool call was in front of them, and they called the reply "transparent".
- The small judge also passed two replies that start with "No." to "Do you deliver to Nunavut?" (we do; only large items are not delivered there), and one French reply without the "5 à 10 jours" fact.

## Why they raised false alarms

Most false alarms came from what the judge could **not** see: the order details returned by the lookup tool (so the item price looked "invented"), and the help-desk phone number, which is in the assistant's instructions, not in the policy sections. The stronger judge was stricter about this missing evidence, so it caught more failures and raised twice as many false alarms.

## Decision

- Use the small judge to **sort** replies for human review, not to approve a release: it finds about 4 in 5 of the failures here.
- Give the judge the same evidence as the assistant (tool results, the facts in the instructions) before trusting its "fail".
- Keep a person on every reply that calls a tool with values the customer did not give: neither judge noticed.
- Check again with your own labels whenever the rubric, the judge model or the app changes. The evaluation course teaches judge calibration in depth.
