# larkfield-match (end-of-m05)

Larkfield's record matching tool, the project of the course *Entity Resolution and Record Matching: Is This the Same Thing?* on Nextia Learning.
It finds the records in Larkfield's three customer lists (and two supplier feeds) that describe the same customer (or product), and measures how well it does it.

This copy is the project at the end of Module 5, *Probabilistic linkage*. It has Fellegi-Sunter weights from labels, Splink on DuckDB without labels, the waterfall of one pair, the match, review and non-match bands. It has 29 tests.

**Every record is synthetic:** our code made it from invented people. No record describes a real person.

## Set up

You need Python 3.12. The course data folder must be next to the project folders (`../../data` from this folder, as in the labs repository) or in the folder that `LARKFIELD_DATA` names.

macOS and Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -e .
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -e .
```

## First commands

```sh
match weights
match splink
match eval --run splink
match bands
python -m pytest -q
```

`match --help` lists every command. `match reset` deletes `outputs/` (the prepared records, pairs, models and clusters) so that you can start again.

## Next

The next copy, `end-of-m06`, adds pair classifiers (logistic regression and LightGBM), active learning, embeddings, calibration and recorded language-model answers for the unsure band.

## Licence

MIT (see `LICENSE`). The course data: CC0 1.0.
