# Capstone starter

This is the start of your capstone: a document support assistant (the standard track) or your own product (the own-idea track). It has no product code yet. It has the design-pack templates that every lesson fills, and a check that your computer is ready.

## First run

You need Python 3.12 or newer, Git, and Docker (Docker Desktop on macOS and Windows).

macOS and Linux:

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.check_setup
python -m pytest
```

Windows (PowerShell): `py -3.12 -m venv .venv`, then `.venv\Scripts\Activate.ps1`, then the same `pip`, `python -m scripts.check_setup` and `python -m pytest`.

`check_setup` prints one line per check: `OK`, or `TODO` with what to do. It changes nothing.

## What is here

- `docs/templates/`: the design pack's templates. `docs/README.md` says which lesson fills which file.
- `scripts/check_setup.py`: the setup check.
- `tests/`: the tests of the setup check and of the templates.

## Choose a track

- **Standard track:** build the same kind of product as the worked capstone, with the supplied two-shop data pack (Module 2). This is a good first portfolio project.
- **Own-idea track:** the same steps, with your own narrow domain and your own documents. Use only documents you may use (permissioned), or write synthetic ones. Never use private documents in a public demo.

Write your choice in `docs/project-brief.md` (copy the template) in the first lesson.

## Reset

Delete `.venv` and create it again. Nothing else is changed by this starter.
