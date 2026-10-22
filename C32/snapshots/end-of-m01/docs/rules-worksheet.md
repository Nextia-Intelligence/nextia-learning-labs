# Rules in documents, rules in code: a worked example

For each rule of `docs/ai-policy.md`: can the platform **enforce it in code**, can a person only **check it in a
review**, or can nobody **check** it at all? And at which control point? The control points are in
`docs/control-points.md`.

| Rule | Enforce in code | Control point | What the code cannot do |
|---|---|---|---|
| 2. Only approved models and providers | yes | model gateway (catalog), network egress rule | stop a person who uses an AI website on a personal phone |
| 3. Card numbers never go to a model | partly | model gateway (guardrail: card numbers redacted), registration (data classes) | find a card number written in words, or in a photo |
| 6. A person approves every change | yes | tool gateway (approval policy and grant) | judge whether the person read the proposal before approving |
| 9. A new model is tested on each system's tasks | partly | the remap gate (each consumer's evaluation) | test a system that has no evaluation: no evidence, no remap |
| 10. Answers are fair, polite and correct | no | review (sampled answers, evaluations) | decide "correct" for one answer at the gateway: it does not know the task |

The other rules are for you to sort (the lesson's practice).
