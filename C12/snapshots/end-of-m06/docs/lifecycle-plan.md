# Lifecycle plan for the ticket-routing adapter (worked example)

**Status of the adapter:** not deployed. The result memo (`docs/result-memo.md`) rejected it: it sent no
ticket that needs a person to one. This plan says what we keep, what would make us try again, and what
would have to be in place before any adapter is deployed. A "do not ship" decision needs a plan too: the
evidence and the files must stay usable for the next attempt.

## 1. What we keep, and where

| Item | Where | Why |
|---|---|---|
| The bundle of the better run (`lora-r8-long`) | `bundle/` (from `python -m adapt bundle lora-r8-long`) | The next attempt starts from evidence, not from memory |
| The configurations | `configs/` | The exact settings of every run |
| The data manifest and the rejected records | `data/prepared/manifest.json`, `rejected.jsonl` | Which records were used, and which were removed and why |
| The saved replies of every system | `runs/predictions/` | The comparison can be repeated without any model |
| The decision and result memos | `docs/` | Why we decided |

## 2. What would make us try again (retraining triggers)

- **New training data that covers the gaps**: reviewed examples of tickets that need a person under each
  rule H1 to H5, and French tickets, with provenance and permission recorded in `data/sources.toml`.
- **A change of the hosted model's price or terms** that makes the current assistant too expensive or
  not allowed for our data.
- **A new base model** with a permissive licence, small enough for our hardware: a new base means a new
  adapter (an adapter works only on the exact base revision it was trained on).

Each trigger starts the same steps: prepare, train one controlled run, compare on dev, decide, and read the
holdout once.

## 3. Before any deployment (if a future adapter passes)

- **Monitoring**: every week, a person reviews a fixed sample of 10 routed tickets and every ticket the
  adapter did not send to a person but a human later escalated. The count of missed escalations is the
  first number on the dashboard.
- **Corrections**: a wrong label found in review goes into a corrections file with the reviewer and the
  date; it changes the training data only through `python -m adapt prepare`, never by hand.
- **Rollback**: the hosted assistant stays configured. Rolling back is a setting, not a new release. The
  base model alone is not a rollback for this task: `python -m adapt verify bundle --base-only` fails every
  check, because the base model does not answer in the JSON format.
- **Compatibility**: `python -m adapt verify` runs at every start. It refuses a bundle whose base-model
  revision or tokenizer differs.

## 4. Licence reviews

| What | Licence now | Review when |
|---|---|---|
| SmolLM2-135M-Instruct (base model) | Apache-2.0 | Before every new base revision |
| Training tickets and labels | CC0 1.0 (made up for the course) | Before adding any real ticket: real tickets need the customer's permission and the removal of personal data |
| The evaluation cases | CC0 1.0; evaluation only | If anyone proposes to train on them (never) |
| peft, transformers, PyTorch | Apache-2.0 / BSD-style | At each version upgrade |
