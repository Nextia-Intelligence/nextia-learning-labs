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

## Reset

To start a module again, copy the snapshot of the previous module from the course's labs repository
(`C12/snapshots/`). To get the course's prepared data back after an exercise, run `python -m adapt prepare`.

## Licences

The code is MIT (`LICENSE`). The data in `data/` is CC0 1.0. The files in `model/` are from
SmolLM2-135M-Instruct, Apache License 2.0 (`model/MODEL.md`).
