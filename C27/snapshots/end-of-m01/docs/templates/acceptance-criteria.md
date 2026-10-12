# Acceptance criteria: <your product's name>

Write this in Module 1 (*Acceptance criteria*), with your user. Every criterion must be testable: a person or a script can say "met" or "not met" without arguing.

## Required behaviour

| ID | Given | When | Then |
|---|---|---|---|
| B1 | <a signed-in member of a shop> | <they ask a question that the documents answer> | <they get an answer with at least one citation to their own shop's document> |
| B2 | | | |

## Quality thresholds

Measured on the held-out questions only (Module 5). Write the number before you measure.

| ID | Measure | Threshold | Why this number |
|---|---|---|---|
| Q1 | <answer correct on answerable questions> | <at least 80%> | <...> |
| Q2 | <abstains on unanswerable questions> | <...> | |

## Access control

| ID | Rule | Checked by |
|---|---|---|
| A1 | <a member of one shop never sees another shop's documents, chunks or answers> | <the isolation checks: 0 leaks> |

## Budget

| ID | Limit | Value |
|---|---|---|
| C1 | <model cost per question> | <...> |
| C2 | <money for the whole project> | <...> |
