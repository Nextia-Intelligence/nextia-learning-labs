# ticket-adapter

The project of the course *Fine-Tuning and Adapting AI Models*. Larkfield's support assistant sorts each
ticket with a large hosted model and a long prompt. Should the team fine-tune a small model of its own
instead? This project answers that question with evidence: what fails, which data may be used, what an
adapter trains, one small training run on your computer's processor (CPU), and a comparison with the
hosted model on the same held-out tickets.

The task is narrow on purpose: read one ticket and answer with one JSON object, exactly:

```json
{"team": "payment", "needs_human": false}
```

The tickets are made up for the course. No real customer wrote them.

<!-- start -->
## Set up

You need Python 3.12 or newer. In a terminal, in this folder:

```sh
python -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
python -m adapt cases
```

`python -m adapt cases` prints `271 cases, version 69bc4c1c556f (the evaluation course's set)` and one
line per split. `python -m adapt --help` lists every command.

The evaluation cases (`data/eval/cases.jsonl`) come from the course *Evaluating and Testing AI Systems*:
`dev` is for choices, `holdout` is for the final decision only, and `contaminated` holds the tickets that
the hosted assistant's prompt was written on. They are never training data.

## Module 1: decide whether to adapt

- `python -m adapt systems` lists the systems whose replies are saved in `runs/predictions/`.
- `python -m adapt failures chat-small` and `python -m adapt failures base-short` sort the mistakes of the
  hosted model and of the small base model into kinds: format, labels, routing, missed, false alarm.
- `python -m adapt score chat-small` scores a system; `--by slice` adds one line per slice.
- `targets.toml` holds the targets, written before any training. `python -m adapt targets chat-small`
  checks a system against them.
- `docs/decision-memo.md` is the go/no-go memo, written before any training.

The small model's replies were recorded with the model that you download in Module 4. You do not need it
yet.

## Module 2: prepare trustworthy training data

- `data/source/` holds the training tickets and their labels; `data/sources.toml` says where each file
  comes from and what it may be used for. `python -m adapt sources` prints it.
- `python -m adapt record T-60003` shows one ticket as a training example.
- `python -m adapt prepare` removes wrong labels, secrets, duplicates and leaks into the evaluation cases,
  takes 200 records per team, splits them into training (900) and validation (100), and writes
  `data/prepared/`. The same input always gives the same files.
- `data/exercise/` is the module's exercise: records that a colleague wants to add.

## Module 3: understand adaptation methods

- `python -m adapt params` counts what full tuning and LoRA train in the real model, from
  `model/config.json` alone (no download). `--rank 4 8 16` and `--targets q_proj v_proj` change it.
- `python -m adapt memory` estimates the memory that training needs, for four methods and four model sizes.
- `docs/method-choice.md` compares the methods for three hardware budgets.

## Module 4: run a controlled experiment

Training needs PyTorch, `transformers` and `peft` (about 900 MB in the virtual environment) and the base
model's weights (about 270 MB). On Windows and Linux, install PyTorch first, from the CPU-only index:

```sh
python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu   # Windows and Linux only
python -m pip install -r requirements-dev.txt
python -m adapt download
```

- `configs/lora-r8.toml` is the course's run; `python -m adapt plan configs/lora-r8.toml` shows its steps.
- `python -m adapt train configs/lora-r8.toml` trains it (2 epochs, 226 steps, 2 threads; about 6 minutes
  on the course's computer). It writes `runs/lora-r8/`: the log, checkpoints, the best and the final
  adapter, a summary. `configs/lora-r8-long.toml` is the second run, with one change (6 epochs; 15 to 20
  minutes). The course's recorded runs are already in `runs/`: delete a run's folder first to train it
  again.
- `python -m adapt train configs/lora-r8.toml --stop-after 100`, then the same command with `--resume`,
  stops and resumes a run from its newest checkpoint.
- `python -m adapt curves lora-r8` shows the training and validation loss; `configs/overfit.toml` is a run
  made to overfit (`python -m adapt curves overfit --every 6`).
- `python -m pytest -m model` runs the tests that need the downloaded model.

## Module 5: evaluate beyond training loss

- `python -m adapt compare` compares every saved system on the same dev cases; `--split holdout` once, at
  the end; `--by slice` for each slice.
- `python -m adapt predict adapter --name my-adapter` runs the adapter of `runs/lora-r8-long` on the dev
  cases again (`--split`, `--adapter`, `--limit`). The other local systems: `base-short`, `base-policy`, `base-choice`.
- `python -m adapt regressions` shows how the base model and the adapter answer 20 general questions.
- `python -m adapt cost` compares the running costs, each number marked measured, price or assumption.
- `docs/result-memo.md` is the result memo: the course's adapter does not ship.

## Module 6: package and maintain the adaptation

- `python -m adapt bundle lora-r8-long` writes `bundle/`: the adapter, `bundle.json` (the base model's ID and
  revision, the tokenizer's SHA-256, the configuration, the data manifest, the evaluation), the model card
  and the fixed checks.
- `python -m adapt verify bundle` loads it and runs the fixed checks; `--merged` merges the adapter into the
  weights first; `--base-only` is the rollback: the base model without the adapter.
- `docs/lifecycle-plan.md` is the plan for monitoring, corrections, retraining and licence reviews.

## Reset

To start a module again, copy the snapshot of the previous module from the course's labs repository
(`C12/snapshots/`). To get the course's prepared data back after an exercise, run `python -m adapt prepare`.

## Licences

The code is MIT (`LICENSE`). The data in `data/` is CC0 1.0. The files in `model/` are from
SmolLM2-135M-Instruct, Apache License 2.0 (`model/MODEL.md`).
