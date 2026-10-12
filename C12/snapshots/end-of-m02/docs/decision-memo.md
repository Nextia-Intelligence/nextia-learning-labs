# Go/no-go memo: adapt a small model for ticket routing? (worked example, written BEFORE training)

**Author:** Priya. **Readers:** Tomás, Kwame, Grace, Omar, Amira. **Status:** go for ONE small experiment;
no decision to deploy.

## 1. The need

Tomás proposes to replace the hosted model for one part of the assistant: reading a ticket and choosing
`{"team", "needs_human"}`. His reasons: cheaper, faster, private, "and it will know our policies".

## 2. What fails today (measured, dev cases, `python -m adapt failures`)

| System | Valid answers | Team | Needs a person caught | False alarms | Decisions |
|---|---|---|---|---|---|
| Hosted assistant (chat-small, long prompt, structured output) | 101/102 | 97/100 | 23/23 | 9 | 90/102 |
| Small base model (SmolLM2-135M-Instruct, short instruction) | 0/102 | 0/100 | 0/23 | 0 | 0/102 |

- The hosted assistant's 12 mistakes: 1 reply cut off (format), 2 wrong teams, 9 false alarms. It misses
  no ticket that needs a person.
- The small model never answers with the JSON object: every reply is prose. That is a **format** failure
  first; we cannot see yet whether it knows the teams.
- **Missing knowledge** (facts that change, such as today's delivery times) is not part of this task.
  Fine-tuning would be the wrong tool for it anyway: retrieval or a tool keeps facts current.

## 3. Alternatives, against the same need

| Option | Fixes | Does not fix |
|---|---|---|
| Keep the hosted assistant | Quality is already high | Cost per ticket, data leaves Larkfield, about 3 s per ticket |
| A better prompt for the small model | Possibly the format | Probably not the routing knowledge of a 135M-parameter model (to be measured) |
| Constrain the small model's output to the 10 valid answers | The format, always | The choice itself |
| Retrieval or tools | Missing facts | Not our problem here |
| A LoRA adapter on the small model | Format and task behaviour, if the data teaches them | Anything the training data does not show (French, rules H2–H5) |

## 4. Targets and constraints (`targets.toml`, written now)

- Quality on dev: valid answers ≥ 0.99, team ≥ 0.95, **every** ticket that needs a person caught, false
  alarms ≤ 12, decisions ≥ 0.88. On holdout once, at the end.
- Operations: median ≤ 1.0 s per answer on a laptop CPU with 2 threads.
- Data: only data we may use for training (made-up tickets, CC0); the evaluation cases are never trained on.
- Budget: one run under 30 minutes and 3 GB of memory on the course computer; no hosted training job.
- Deployment: the adapter must load on a pinned base-model revision, pass fixed checks, and be easy to roll
  back to the hosted assistant.

## 5. Decision

Go for one small, controlled experiment. Stop if it cannot meet the needs-a-person target: a model that
misses a safety ticket is not acceptable at any price.
