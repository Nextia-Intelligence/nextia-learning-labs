# larkfield-experiments: the end of Module 2

Larkfield's traffic simulator (`sim`) and analysis tool (`xp`), the project of the course *Experiments and Causal Impact: Did Our Change Work?*. The simulator knows the true effect of every change, so you can check each of your answers with `xp check`.

All data is synthetic: the simulator makes it. There are no real people.

## Set up (Python 3.12)

macOS and Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pytest -q
sim run --scenario email
xp analyse
xp check
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pytest -q
sim run --scenario email
xp analyse
xp check
```

## Commands

| Command | What it does |
|---|---|
| `sim list` | the scenarios: what each one simulates |
| `sim run --scenario email` | run a scenario; its data goes to runs/email-s40/ |
| `sim about email` | what a scenario simulates, and its planted problem if it has one |
| `xp analyse` | the difference B − A of the last run, its 95% interval and p-value (--metric) |
| `xp naive launch` | the naive answers to distrust: before against after, users against non-users |
| `xp check` | compare your last analysis with the true effect that the simulator knows |
| `xp reset` | delete all runs and start again |
| `xp power --baseline 0.09 --mde 0.01 --per-day 4000` | sample size, power and duration (--simulate 200 checks the formula by simulation) |
| `xp plan new reminder-email` | write a test plan before the test; xp plan check FILE checks it |

Every command has `--help`. Runs go to `runs/` (set `LARKFIELD_RUNS` to use another folder).

## Licence

MIT (see `LICENSE`).
