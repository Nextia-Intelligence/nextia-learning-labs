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

## Files

| Path | What |
|---|---|
| `config/costs.json` | The cost of each kind of mistake (assumptions, with the reason for each). |
| `config/rules.json` | The keyword rules. Change them; `route reset` puts them back. |
| `config/prices.json`, `config/compute.json` | The price of the hosted models and of computer time. Prices change: check the current price page. |
| `larkroute/` | The code. Each command is one file in `larkroute/commands/`; each method is in `larkroute/methods/`. |
| `data/` | The inbox (after `get_data.py`). |
| `tests/` | `python -m pytest` |

## Tests

```sh
python -m pytest -q
ruff check .
```

## Licence

MIT (see `LICENSE`). The data is CC0.
