# Result memo: the ticket-routing adapter (worked example)

**Author:** Priya. **Decision:** **do not ship the adapter.** Keep the hosted assistant. Keep the evidence
and the bundle for a later attempt (`docs/lifecycle-plan.md`).

## 1. What we tried

Two LoRA adapters (rank 8, query and value layers, 460,800 trainable parameters, a 1.9 MB file) on
SmolLM2-135M-Instruct, trained on the CPU on 900 cleaned training records (`configs/lora-r8.toml`, 2
epochs; `configs/lora-r8-long.toml`, the same with 6 epochs). We chose the second on the dev cases and the
validation loss (0.0193 vs 0.0584), and then read the holdout cases once.

## 2. Results on the same held-out cases (`python -m adapt compare`)

| System | Valid answers | Team | Needs a person caught | False alarms | Decisions | Median s/answer |
|---|---|---|---|---|---|---|
| dev: hosted assistant (chat-small) | 101/102 | 97/100 | **23/23** | 9 | 90/102 | 2.98 (hosted) |
| dev: word counts + safety words | 102/102 | 86/100 | 6/23 | 1 | 74/102 | < 0.001 |
| dev: small model, better prompt | 101/102 | 22/100 | 8/23 | 25 | 12/102 | 0.41 |
| dev: adapter, 6 epochs | 102/102 | 89/100 | **0/23** | 0 | 74/102 | 0.24 |
| holdout: hosted assistant | 98/98 | 97/97 | 24/24 | 4 | 94/98 | 2.81 (hosted) |
| holdout: adapter, 6 epochs | 98/98 | 87/97 | **0/24** | 0 | 65/98 | 0.24 |

Against `targets.toml` the adapter meets the format and speed targets and misses the others.

## 3. What the evidence says

- **Fine-tuning fixed the format.** The base model never answered in JSON (0/102); the adapter always did
  (102/102). A better prompt fixed most of the format too (101/102), but not the routing (22/100).
- **It learned the teams, not the safety rule.** Team 89/100 on dev and 87/97 on holdout. With no French
  training record it got 7 of 10 French decisions right on dev, but 1 of 10 on holdout: 10 cases are too
  few to say anything about French. And it sent **no** ticket to a person: 0 of 23 on dev, 0 of 24 on
  holdout.
- **Why:** only 78 of the 900 training records need a person, all under rule H1; none shows rules H2 to
  H5. The adapter's probability of `true` for the 9 validation records that need a person is at most 0.48:
  never above the 0.5 that greedy decoding needs. A lower threshold would catch some, with false alarms
  (dev at 0.1: 8 of 23 caught, 3 false alarms; `runs/probes/lora-r8-long.json`). That is a patch, not a fix.
- **Lower training loss was not the goal.** The second run had a much lower validation loss and better
  routing, and exactly the same safety result.
- **Regressions:** on 20 general questions the base model answered 12 right, the adapters 10 and 11. Too
  few questions to say more than "no large loss".
- **Cost:** the hosted assistant costs about US$0.35 per 1,000 tickets (measured). The adapter would save
  about US$8.53 a month at 822 tickets a day (an assumption), and keep the tickets on our computers.
  Hosting a fine-tuned model in the cloud instead would cost US$1.70 an hour (price), far more than the
  hosted assistant.

## 4. What would change the decision

Reviewed training examples of every needs-a-person rule and of French tickets; or a design where the
adapter only routes and the safety decision stays with the hosted model or a person. Either one must be
measured again on dev, and then once on a new holdout version: this memo read the current holdout cases,
so they are no longer unseen.
