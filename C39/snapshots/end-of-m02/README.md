# larkfield-match (end-of-m02)

Larkfield's record matching tool, the project of the course *Entity Resolution and Record Matching: Is This the Same Thing?* on Nextia Learning.
It finds the records in Larkfield's three customer lists (and two supplier feeds) that describe the same customer (or product), and measures how well it does it.

This copy is the project at the end of Module 2, *Clean first, then match exactly*. It has normalising, a small parser for names and addresses, the four rules, results by source and by practice problem, `match compare`. It has 16 tests.

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
match normalise G-000002
match eval --run rules
match eval --run rules --by problem
python -m pytest -q
```

`match --help` lists every command. `match reset` deletes `outputs/` (the prepared records, pairs, models and clusters) so that you can start again.

## Next

The next copy, `end-of-m03`, adds the all-pairs estimate, blocking keys, sorted neighbourhood, MinHash LSH for product titles, pair completeness and reduction ratio.

## Licence

MIT (see `LICENSE`). The course data: CC0 1.0.
