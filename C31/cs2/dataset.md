# Dataset card: Terminal-Bench 2.0, Terminus 2 runs (reduced)

Used by: the case study *The cost of a coding agent* of the course *Observability for AI Agents: Traces, Costs and
Audit Trails* (Nextia Learning), project `coding-agent-cost/`.

| Field | Value |
|---|---|
| Source | https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard, submissions `Terminus2__DeepSeek-V3.2` (job `2026-02-07__07-47-43`) and `Terminus2__Claude-Opus-4.6` (jobs `2026-02-05__16-08-28`, `2026-02-05__17-41-47`) |
| Publisher / creator | The Terminal-Bench team (agent Terminus 2, https://www.tbench.ai/terminus), on Hugging Face as `harborframework` |
| Licence | Apache License 2.0 (the dataset card's `license: apache-2.0`); full text in `data/runs/LICENSE-terminal-bench-leaderboard.txt` |
| Attribution text | "Contains data from the Terminal-Bench 2.0 leaderboard (harborframework/terminal-bench-2-leaderboard), Apache-2.0, reduced by Nextia Learning: all text removed." |
| Version | Hugging Face revision `572b2614be2c0cb2527e14f5b1e4026f1072e6c1` |
| Files used | `data/runs/terminus2-deepseek-v3.2.jsonl.gz`, `data/runs/terminus2-claude-opus-4.6.jsonl.gz`, kept in `data/`: yes (the licence allows it) |
| SHA-256 | in `data/runs/SHA256SUMS` (the project checks them before it reads a file) |
| Size | DeepSeek-V3.2: 445 runs, 10,966 model calls, 0.51 MB. Claude Opus 4.6: 445 runs, 6,663 model calls, 0.27 MB |

## What one row means

One line is one **run**: one attempt of the Terminus 2 agent at one of the benchmark's 89 terminal tasks (build a
program, fix a bug, port code, train a small model …), with each **model call** of the run. Each task was run 5
times with each model. A run is *solved* when the task's tests passed (`reward` 1.0), *failed* when they did not,
*timed out* when the agent hit the task's time limit (`exception` `AgentTimeoutError`) and the tests did not pass,
and *error* when the benchmark could not check it.

Each model call (`steps[]`) has: `t` (seconds from the run's first step to this answer), `prompt` (input tokens,
cached ones included), `cached` (input tokens served from the provider's cache), `completion` (output tokens),
`cost` (US$ as the submitter's software computed it, if it did), `programs` (the first word of each command the model
sent to the terminal, "" for an empty command) and `digests` (the first 10 hex characters of the SHA-256 of each
command's exact keystrokes: two equal digests mean the same command).

## Why this dataset

It is an open set of **coding-agent** runs with the token counts of **every** model call, the cached part, the
commands and the result of tests, under a licence that allows copies. The same agent ran the same tasks with two
models, so the second model is a fair "new input". Open SWE-agent, SWE-smith and OpenHands trajectories have no
token counts (or only run totals, or no clear licence): see the case study's research notes.

## Changes we made

- Kept two submissions of the Terminus 2 agent (DeepSeek-V3.2 and Claude Opus 4.6), all 445 trials of each.
- **Removed all text:** the instructions, the model's messages, the terminal output and the commands' text. A
  command is kept as its first word and a short digest only.
- Kept per run: the trial name, task, model (provider prefix removed), reward, exception type, start time, agent
  seconds, run totals; per call: the fields above. Runs are ordered by start time.

## Limitations and cautions

- **A benchmark, not your team's work.** 89 tasks chosen to be hard, each in a fresh container with a time limit.
  Your agent's tasks, lengths and costs will differ: measure your own runs.
- **Prices are assumptions.** The project prices tokens with its own table (`prices.json`). For DeepSeek-V3.2 it
  gives every recorded cost exactly. For Claude Opus 4.6 it gives 3.7% less than the recorded cost: the records do
  not say how many tokens were written to the cache, which costs more than normal input.
- **Times are the benchmark's.** `t` is the time between answers: the model's time and the terminal's time
  together. Many runs ran at the same time on the submitter's machines.
- **A digest says "the same command", not "the same situation".** An empty command can be an honest wait (for a
  compiler) or a loop.
- One run of DeepSeek-V3.2 ended in an error of the benchmark (no result file): it is counted, as "error".
