# Recorded runs

Everything the course trained and measured, so that every lesson works without training. The same files
are in the project snapshots (`runs/` in `end-of-m04` and later). The base model is SmolLM2-135M-Instruct
at revision `12fd25f7`; every run used the processor (CPU) with 2 threads.

| Folder | What it has |
|---|---|
| `lora-r8/` | The first run (`configs/lora-r8.toml`: 900 records, 2 epochs, 226 steps): `log.jsonl` (training loss per step, validation loss every 25 steps), `summary.json`, the final `adapter/` and the `best/` adapter |
| `lora-r8-long/` | The second run, with one change: 6 epochs (678 steps) |
| `overfit/` | A run made to overfit on purpose: 48 records, 20 epochs |
| `predictions/` | The replies of every system to the 271 evaluation cases (`systems.json` says what each system is). `chat-small.jsonl` was recorded from the hosted model in the course *Evaluating and Testing AI Systems* |
| `general/` | The answers of the base model and of each adapter to 20 general questions |
| `probes/` | For each adapter: its probability of `true` for `needs_human`, case by case |

Times in the logs are from one computer while other programs ran; they change from computer to computer.
The losses, replies and scores do not change.
