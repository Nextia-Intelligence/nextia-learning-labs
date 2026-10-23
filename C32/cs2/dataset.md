# Dataset card: tau2-bench telecom trajectories (a fixed sample of counts, names and arguments)

Used by: the case study *Contain a runaway agent* (course *Governing AI Agents: Gateways, Registries and Controls*), project folder `runaway-replay`

| Field | Value |
|---|---|
| Source | https://github.com/sierra-research/tau2-bench, folder `data/tau2/results/final` (the results of the τ²-bench paper) |
| Publisher / creator | Sierra Research (τ²-bench: Barres, Dong, Ray, Si and Narasimhan, 2025, arXiv:2506.07982) |
| Licence | MIT, https://github.com/sierra-research/tau2-bench/blob/v1.0.0/LICENSE (the licence text is in `trajectories/LICENSE-tau2-bench.txt`, as the licence asks) |
| Attribution text | "Trajectories from τ²-bench by Sierra Research (MIT licence), https://github.com/sierra-research/tau2-bench. Reduced to token counts, tool names and arguments by Nextia Learning." |
| Version or access date | Release v1.0.0 (commit 17e07b1da2bbc0cadfddeea36412686e0604127b). The same files, with the same Git blob IDs, are in every later release. The runs were recorded in June 2025. |
| File used | Four reduced files, kept in `trajectories/`: yes (the MIT licence allows copies with its notice) |
| SHA-256 | `telecom-gpt-4.1-mini.jsonl.gz` 3fd5bbdf80748b6570a4e593b5e1f7c69602ad09a47234c02d2a8465d19122f5 · `telecom-gpt-4.1.jsonl.gz` 72e1bcaa45215f49e29fcc09ef00f438c9df4ad65be55c0ac7286ba8b71f104e · `telecom-o4-mini.jsonl.gz` 28d92f3ac4819e035f3dc593e16a7bb6ad566a3b38b5c97da476998816e18193 · `telecom-claude-3.7-sonnet.jsonl.gz` 61209031eb49ebf204cc132949e96f5104febc9ff592b5da39647d3ec149a2b1 (also in `trajectories/SHA256SUMS`) |
| Size | 4 files × 456 runs (114 tasks × 4 trials); 13,269 + 7,785 + 8,070 + 8,042 model calls; 0.63 MB in all (the original files: 166 MB) |

## What one row means

One row is one **run**: one conversation between an AI support agent of a phone company and a customer played by another model (gpt-4.1). For each of the agent's model calls, the row has the recorded token counts and the tools that the model asked for, with their arguments. The row says how the run ended: **success** (the benchmark's reward is 1), **failure** (reward 0, the conversation ended normally) or **runaway** (the benchmark stopped it at 200 messages or 10 tool errors).

| File | Agent model | Runs: success / failure / runaway | Use in the case study |
|---|---|---|---|
| `telecom-gpt-4.1-mini.jsonl.gz` | gpt-4.1-mini-2025-04-14 | 200 / 224 / 32 | the design day: choose the limits |
| `telecom-gpt-4.1.jsonl.gz` | gpt-4.1-2025-04-14 | 156 / 297 / 3 | new input: the limits on another model |
| `telecom-o4-mini.jsonl.gz` | o4-mini-2025-04-16 | 192 / 264 / 0 | new input: the limits on another model |
| `telecom-claude-3.7-sonnet.jsonl.gz` | claude-3-7-sonnet-20250219 | 225 / 230 / 1 | "Go further": a fourth model |

## Why this dataset

The case study needs real agent runs that record **the tokens of every model call**, **the tool calls with their arguments**, and **how each run ended**, with some runs that loop. τ²-bench's published results have all four, under the MIT licence: the gpt-4.1-mini runs include 32 real loops (the agent asks for the same customer, line, device and plan again and again until the benchmark stops it).

Compared (details in the course's research notes):

- **nebius/SWE-agent-trajectories** (Hugging Face, CC BY 4.0, 80,036 runs, about 1.1 GB): real coding-agent runs with a success label, but **no token counts** (we would have to estimate them), and every run is large.
- **SWE-bench/SWE-smith-trajectories** (Hugging Face, MIT, about 3.2 GB): the same problem: messages and a success label, no token counts.
- **nebius/SWE-rebench-openhands-trajectories** (CC BY 4.0, about 2 GB): no token counts either.
- **SWE-bench/experiments** (GitHub): SWE-agent's trajectory files have token counts, but the repository states **no licence**, so we may not copy it.
- **τ²-bench retail results** (MIT): the same format, but none of the 1,824 retail runs we checked looped (every one ended normally).

## Changes we made

`tools/make_sample.py` read each original results file and kept, for each run: its ID, task, trial, why it ended, its reward, its recorded cost, and for each of the agent's model calls: the prompt and completion tokens, the recorded cost, and each tool call's name, arguments and error flag. **We removed every text**: the messages, the tool results and the agents' policy. We removed nothing else and changed no value. The user simulator's own model calls are not in the sample: they are not the agent's calls and would not pass the agent's gateway.

## Limitations and cautions

- **A benchmark, not a production log.** The customers are simulated by a model, and the tasks are a test set (114 tasks, each run 4 times). The day in the case study is these 456 runs in a fixed shuffled order: a constructed day.
- **The costs are a floor.** The benchmark stopped each runaway at 200 messages (at most 100 model calls of the agent). Without that stop, a real loop goes on.
- **One price for every token.** The case study prices every recorded token at the course's chat-small price (US$0.10 in, US$0.50 out per million), not at the price of the model that made it. The recorded costs in the files are the benchmark's own and include provider discounts that the token counts do not show.
- **The customer details in the arguments are made up** by the benchmark (for example "John Smith", 555 phone numbers). They are not real people.
- **Success is the benchmark's reward**: the database ended in the right state and the agent said the right things. It is not a measure of the customer's satisfaction.
