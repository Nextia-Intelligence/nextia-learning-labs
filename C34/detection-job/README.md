# The detection job

A small job that runs once a day. It reads Larkfield's new card payments, scores them, keeps the alerts that
Sofia's team can review (50 a day), groups them, and writes each alert with its reasons. A rerun of the same
day never sends an alert twice. It belongs to the course **Anomaly Detection: Find What Is Unusual**
(Module 9, *Run a detector in production*) on [learning.nextia-ai.com](https://learning.nextia-ai.com).

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
| `python -m detect score --day 2025-10-01` | Show the day's most unusual payments. Nothing is sent. |
| `python -m detect run --day 2025-10-01` | Score, group, keep the budget, and write the new alerts to `alerts/2025-10-01.jsonl`. |
| `python -m detect replay --from 2025-10-01 --to 2025-10-31` | Run every day of a period, as the schedule would. |
| `python -m detect drift --day 2025-10-31` | Compare the last 7 days with the training days: has normal moved? |
| `python -m detect review ALERT_ID real` | Save a reviewer's answer (`real` or `not`). |
| `python -m detect report --week-ending 2025-10-31` | The weekly alert report. |

Settings (environment variables): `DETECT_BUDGET` (50 alerts a day), `DETECT_POLICY` (`budget`: the 50 most
unusual alerts every day; `fixed`: every alert above the threshold learned from the training days),
`DETECT_DATA` (`data`), `DETECT_STATE` (`state`), `DETECT_ALERTS` (`alerts`).

## Run it every day

The job is a command, so any scheduler can run it. For example, at 06:00 every day for the day before:

- Linux (cron): `0 6 * * * cd /path/to/detection-job && .venv/bin/python -m detect run --day $(date -d yesterday +\%F)`
- Windows: Task Scheduler, a daily task that runs `.venv\Scripts\python.exe -m detect run --day <yesterday>`
  in this folder.

The MLOps course shows how to run jobs like this one in production, with dashboards and incidents.

## Reset

Delete the folders `state/` and `alerts/`. Then train again.

## Tests

```sh
python -m pytest -q
ruff check .
```
