# larkfield-match (end-of-m08)

Larkfield's record matching tool, the project of the course *Entity Resolution and Record Matching: Is This the Same Thing?* on Nextia Learning.
It finds the records in Larkfield's three customer lists (and two supplier feeds) that describe the same customer (or product), and measures how well it does it.

This copy is the project at the end of the course. It has a week of new records every day, the review queue, timing at larger sizes, privacy (hashed and encoded values) and deletion requests. It has 42 tests.

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
match golden
match daily --day 1
match review --show 5
match bench
python -m pytest -q
```

`match --help` lists every command. `match reset` deletes `outputs/` (the prepared records, pairs, models and clusters) so that you can start again.

PyTorch is in the requirements for the embedding lesson. The course data has every embedding already, so no command downloads the model unless you ask for new embeddings.

## Licence

MIT (see `LICENSE`). The course data: CC0 1.0.
