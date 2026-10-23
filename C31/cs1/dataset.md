# Dataset card: tau2-bench retail runs (a fixed sample of times, counts, tool names, arguments and grades)

Used by: the case study *Find failures in public agent runs* (course *Observability for AI Agents: Traces, Costs and Audit Trails*), project folder `public-agent-runs`

| Field | Value |
|---|---|
| Source | https://github.com/sierra-research/tau2-bench, folder `data/tau2/results/final` (the results of the τ²-bench paper) |
| Publisher / creator | Sierra Research (τ²-bench: Barres, Dong, Ray, Si and Narasimhan, 2025, arXiv:2506.07982) |
| Licence | MIT, https://github.com/sierra-research/tau2-bench/blob/v1.0.0/LICENSE (the licence text is in `runs/LICENSE-tau2-bench.txt`, as the licence asks) |
| Attribution text | "Agent runs from τ²-bench by Sierra Research (MIT licence), https://github.com/sierra-research/tau2-bench. Reduced to times, token counts, tool names, arguments and grades by Nextia Learning." |
| Version or access date | Release v1.0.0 (commit 17e07b1da2bbc0cadfddeea36412686e0604127b). The runs were recorded in June 2025 (the timestamps in the files). |
| File used | Four reduced files of runs and one file of the tasks' expected actions, kept in `runs/`: yes (the MIT licence allows copies with its notice) |
| SHA-256 | `retail-claude-3.7-sonnet.jsonl.gz` 8d1503d28e41a9ed00b98eb8537b6e908fafdbd5deb62cf0b58c7533436b2ca0 · `retail-gpt-4.1-mini.jsonl.gz` ac4699cfce44900333646433fb5d2724c01e14604cb0036e587f46e705660659 · `retail-gpt-4.1.jsonl.gz` b27fd880cc5e218b0fe67d36c2b76cf274328a8888ea901e318bf09f4e3f7ca5 · `retail-o4-mini.jsonl.gz` 13209f0ef271a31491fdd51d79da1a184c26afbdc2f8669910db05b29955c07c · `retail-tasks.jsonl.gz` e154eaea8e58ff2a3828763311755ff9e79204edab5a49efd7985b2f32050464 (also in `runs/SHA256SUMS`) |
| Size | 4 files × 456 runs (114 tasks × 4 trials); 5,104 + 5,953 + 5,668 + 6,287 model calls; 1.3 MB in all (the original files: 92.7 MB) |

## What one row means

One row is one **run**: one conversation between an AI customer-service agent of an online shop and a customer played by another model (gpt-4.1). The customer wants to cancel or change an order, return or exchange items, or change an address. The row has each message's time and sender, the agent's token counts and recorded cost for each model call, the tools the agent asked for with their arguments, whether each tool answered with an error (and the error's short text), and how the customer ended the conversation. The **grade** is the benchmark's: reward 1 when the shop's database ended as the task expects and the agent told the customer what the task says, otherwise 0.

| File | Agent model | Runs | Failed (reward 0) | Use in the case study |
|---|---|---|---|---|
| `retail-gpt-4.1.jsonl.gz` | gpt-4.1-2025-04-14 | 456 | 118 | the design runs: find the patterns and adapt the rules |
| `retail-claude-3.7-sonnet.jsonl.gz` | claude-3-7-sonnet-20250219 | 456 | 97 | new input, end to end |
| `retail-o4-mini.jsonl.gz` | o4-mini-2025-04-16 | 456 | 130 | new input |
| `retail-gpt-4.1-mini.jsonl.gz` | gpt-4.1-mini-2025-04-14 | 456 | 155 | new input |
| `retail-tasks.jsonl.gz` | — | 114 tasks | — | the expected actions of each task (the benchmark's answer key), to say why a run failed |

## Why this dataset

The case study needs real agent runs of a customer-service agent with **the time of every step**, **the token counts of every model call**, **the tool calls with their arguments and errors**, and **a grade** that says which runs failed. τ²-bench's published results have all four, under the MIT licence, and its retail domain is a shop's support desk with orders, returns and refunds.

Compared (details in the course's research notes):

- **τ²-bench telecom** (MIT): the same format, but the agents governance course's case study already uses it.
- **τ²-bench airline** (MIT, 200 runs a model, 7.6–10.5 MB a file): the same format, fewer runs (50 tasks × 4).
- **τ-bench historical trajectories** (sierra-research/tau-bench, MIT, 4–27 MB a file): the earlier benchmark's runs, with a reward, but **no timestamps and no token counts**, so a trace would have no times and no cost.
- **Salesforce/APIGen-MT-5k** (Hugging Face): multi-turn agent conversations, but under **CC BY-NC 4.0** (no commercial use), which the course does not use.
- **nvidia/When2Call** (Hugging Face, CC BY 4.0): single tool-calling decisions, not whole runs, and no times.

## Changes we made

`tools/make_sample.py` read each original results file and kept, for each run: its ID, task, trial, timestamps, why it ended, the agent's and the customer simulator's recorded cost, and for each message: its sender and time; for the agent's model calls, the token counts, the recorded cost, the finish reason, whether it wrote text to the customer (yes or no) and each tool call's name and arguments; for each tool answer, whether it was an error and the error's short text; for the customer's messages, the end token (###STOP###, ###TRANSFER###, ###OUT-OF-SCOPE###). The benchmark's grade went into a separate `grade` object. **We removed every other text**: the agent's and the customer's words, the tool results and the agent's policy. We changed no value.

## Limitations and cautions

- **A benchmark, not a production log.** The customers are simulated by a model, and the tasks are a test set (114 tasks, each run 4 times). The runs were made in batches, so their start times are close together.
- **The time zone is not recorded.** The converter reads the timestamps as UTC.
- **The costs are the benchmark's**, recorded with its prices of the time, not the course's price table.
- **The customer details in the arguments are made up** by the benchmark (names, e-mail addresses, zip codes). They are not real people. The converter still keeps them off the spans: it records the argument names and a digest.
- **The grade is the benchmark's**: the database ended in the expected state and the agent said what the task requires. It is not a measure of the customer's satisfaction, and a few tasks may have more than one acceptable answer.
