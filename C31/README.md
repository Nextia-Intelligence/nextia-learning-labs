# Observability for AI Agents: Traces, Costs and Audit Trails

The files of the course *Observability for AI Agents: Traces, Costs and Audit Trails* (Nextia Learning).

| Folder | What it is |
|---|---|
| `snapshots/` | The course project at every stage: `start`, then `end-of-m01` to `end-of-m08` (the end of each module). Each lesson says which one to copy. |
| `data/` | The saved telemetry of the replayed week, the healthy week, a constructed run and the gateway run, and the start's log file, with their dataset card (`data/dataset.md`). Every snapshot from Module 1 has the same files in `data/telemetry/`. |
| `inspector/` | The run inspector: a small app that opens the saved week (or your own Grafana stack) and shows runs, one run, its audit story, cost and two runs side by side. You use it; you do not build it. |
| `data/langfuse/` | The answers of Langfuse's API that the course team saved after one run of the week: the double refund's session (`session-R-1014-040.json`), its scores and a sample of observations. Use them if you do not want a Langfuse account. |
| `cs1/` | Case study *Find failures in public agent runs*: `starter.zip`, `finished.zip` and the dataset card. |
| `cs2/` | Case study *The cost of a coding agent*: `starter.zip`, `finished.zip` and the dataset card. |
| `cs3/` | Case study *Could the records have answered?*: `starter.zip`, `finished.zip` and the dataset card. |

You need Python 3.12 and a terminal. No account, no key and no money: every model decision is a real recording,
replayed, and every change goes to a practice database on your computer. Docker (for Grafana) and a Langfuse
account are optional, and each lesson says so before you need them.

The practice data is made up; no real customer wrote it. Code: MIT licence. Data: CC0 (see `data/dataset.md`).
