# The detection job (start)

The start of the detection job of the course **Anomaly Detection: Find What Is Unusual** (Module 9,
*Run a detector in production*) on [learning.nextia-ai.com](https://learning.nextia-ai.com). It can already
learn "normal" and score a day. In the lessons of Module 9, you turn the scores into alerts that a team
can trust.

The data is synthetic: no real people and no real cards. The anomalies in it are ones we planted on purpose.

## Set up (Python 3.12)

macOS or Linux:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/get_data.py
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/get_data.py
```

`get_data.py` downloads `payments.csv.gz` (about 6 MB) into `data/` and checks its SHA-256.

## Use it

| Command | What it does |
|---|---|
| `python -m detect train --until 2025-09-30` | Learn "normal" from the 60 days up to that day (Isolation Forest on behaviour features). |
| `python -m detect score --day 2025-10-01` | Show the day's most unusual payments. |

## Reset

Delete the folder `state/`. Then train again.

## Tests

```sh
python -m pytest -q
ruff check .
```
