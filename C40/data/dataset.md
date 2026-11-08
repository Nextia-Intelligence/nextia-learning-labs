# Dataset card: Larkfield experiments (synthetic)

Used by: the lesson notebooks of the course *Experiments and Causal Impact: Did Our Change Work?*

| Field | Value |
|---|---|
| Source | Made by the course simulator (`snapshots/*/larkfield_experiments/`), with each scenario's default seed |
| Publisher / creator | Nextia Learning |
| Licence | CC0 1.0 (the synthetic data); the project code is MIT |
| Attribution text | None needed |
| Files | `email/`, `logs/`, `launch/`, `delivery/`, `regions/`, `prompt/` (each with `scenario.json` and `truth.json`), `support_answers.jsonl`; checksums in `SHA256SUMS` |

## What one row means

- `email/customers.csv.gz`: one customer in the reminder-email test (60,000 customers): the variant (A no email, B the email), the customer's history, and whether they ordered in the 14 days after the email.
- `logs/customers.csv.gz`: one customer in the 28 days after the recommendation block's launch (40,000 customers): whether they used the block, and what they spent. No test.
- `launch/daily.csv`: one day of orders and sales, September 2024 to November 2025; `counterfactual.csv`: the same days without the block (the simulator's truth).
- `delivery/customers.csv.gz`: one customer in the free-delivery test (28 days).
- `regions/areas_weekly.csv`: one delivery area and one week of sales (60 areas, 78 weeks); `provinces_weekly.csv`: the same by province.
- `prompt/tickets.csv.gz`: one support ticket in the prompt test.
- `support_answers.jsonl`: one recorded answer of the support assistant: a question, the prompt (A or B), the answer and its tokens.

## Why this dataset

A simulator knows what would have happened without each change, so every lesson can check its estimate against the
true effect (`truth.json`). Real data never shows the counterfactual.

## Changes we made

None: these are the simulator's outputs. Some scenarios have problems planted on purpose (the scenario's
`sim about` text says which).

## Limitations and cautions

The customers, prices and effects are made up and simpler than a real shop. The true effects are ours, by design:
use the data to learn the methods, not to learn about real customers. The support answers were recorded once from a
language model (Azure OpenAI, the course's small chat deployment) for synthetic questions; a new run would give
other words.
