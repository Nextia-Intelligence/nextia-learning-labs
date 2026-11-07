# larkroute: Larkfield's message router

This is the project of the course *Text Classification and Routing: Send Each Message to the Right Place* on [Nextia Learning](https://learning.nextia-ai.com/courses/text-routing/). It sends each support message to the right team, with a confidence, and it sends the unsure messages to a person.

The Larkfield inbox is **synthetic**: we made it for the course. It has no real people. The answers of the hosted models were **recorded once**, so you need no key and no account.

## Set up (once)

You need Python 3.12.

macOS or Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python get_data.py
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python get_data.py
```

`get_data.py` downloads the inbox into `data/` (about 6 MB) and checks every file. You should see `Ready: … files in data/, every checksum is right.`

## First run

```sh
route info
route compare --quick
```

`route compare --quick` scores three ways to route the test messages: a person reads everything, keyword rules (and a person for the rest), and TF-IDF with logistic regression. It prints one row for each, with the accuracy and the cost of the mistakes per 1,000 messages.

## Commands

| Command | What it does |
|---|---|
| `route info` | The data: messages, splits, routes, languages and channels; checks the files. |
| `route compare` | Trains and scores methods on the same messages and the same cost table. `--quick`, `--methods "a,b"`, `--split validation`, `--labels old`. |
| `route reset` | Deletes what the commands wrote (`models/`, `runs/`, `queue/`), puts back the configuration files, and downloads any data file that is missing or changed. |
| `route agreement` | How often two people gave the same route (agreement and Cohen's kappa). |
| `route explain MESSAGE_ID` | The words that made the TF-IDF model choose a route. |
| `route llm MESSAGE_ID` | The recorded LLM answer for one message, with its tokens, cost and time. |
| `route cascade` | TF-IDF first, the LLM for the unsure messages, a person for the rest. `--search` chooses the thresholds on validation. |
| `route calibration` | Is a confidence of 0.9 right 9 times in 10? The reliability table. |
| `route zones` | Chooses the decide, review and person zones under a review limit (`--review-max 0.10`). |
| `route corrections` | The agents' queue moves to check before they become labels. |
| `route train --version v1 --make-current` | Trains and saves a model version with its thresholds. |
| `route serve` | Runs the routing service on `http://127.0.0.1:8036` (stop it with Ctrl+C). |
| `route drift` | Replays the launch month week by week; `--topics` groups the unsure messages. |
| `route release --candidate v2` | Compares a new model with the current one by slice; makes it current only if it passes. `--rollback` goes back. |

## The routing service

```sh
route train --version v1 --make-current
route serve
```

In a second terminal (macOS or Linux):

```sh
curl -s http://127.0.0.1:8036/route -H 'content-type: application/json' \
  -d '{"message_id": "M-999001", "text": "Tracking says my parcel was delivered yesterday, but nothing is at my door. Order LK-123456.", "channel": "chat"}'
```

Windows (PowerShell):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8036/route -ContentType 'application/json' `
  -Body '{"message_id": "M-999001", "text": "Tracking says my parcel was delivered yesterday, but nothing is at my door. Order LK-123456.", "channel": "chat"}'
```

Every answer has the route, the zone (`decide`, `review` or `person`), the confidence, the model version and the label version. The service writes `queue/decisions.jsonl` (no message text) and `queue/review_queue.jsonl`.

## Files

| Path | What |
|---|---|
| `config/costs.json` | The cost of each kind of mistake (assumptions, with the reason for each). |
| `config/rules.json` | The keyword rules. Change them; `route reset` puts them back. |
| `config/prices.json`, `config/compute.json` | The price of the hosted models and of computer time. Prices change: check the current price page. |
| `larkroute/` | The code. Each command is one file in `larkroute/commands/`; each method is in `larkroute/methods/`. |
| `data/` | The inbox (after `get_data.py`), the recorded answers (`data/recordings/`) and the recorded predictions (`data/predictions/`). |
| `tests/` | `python -m pytest` |

## Tests

```sh
python -m pytest -q
ruff check .
```

## Licence

MIT (see `LICENSE`). The data is CC0.
