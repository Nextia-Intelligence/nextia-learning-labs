# larkfield-match (end-of-m07)

Larkfield's record matching tool, the project of the course *Entity Resolution and Record Matching: Is This the Same Thing?* on Nextia Learning.
It finds the records in Larkfield's three customer lists (and two supplier feeds) that describe the same customer (or product), and measures how well it does it.

This copy is the project at the end of Module 7, *From pairs to entities*. It has safe clustering, cluster measures (B-cubed), golden records with stable IDs, undo. It has 38 tests.

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
match cluster --run lgbm --method safe
match golden
match eval --run lgbm
python -m pytest -q
```

`match --help` lists every command. `match reset` deletes `outputs/` (the prepared records, pairs, models and clusters) so that you can start again.

PyTorch is in the requirements for the embedding lesson. The course data has every embedding already, so no command downloads the model unless you ask for new embeddings.

## Next

The next copy, `end-of-m08`, adds a week of new records every day, the review queue, timing at larger sizes, privacy (hashed and encoded values) and deletion requests.

## Licence

MIT (see `LICENSE`). The course data: CC0 1.0.
