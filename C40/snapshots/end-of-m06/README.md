# larkfield-experiments: the end of Module 6

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

This stage adds DoWhy (and its dependencies): the first install takes a few minutes.

## Commands

| Command | What it does |
|---|---|
| `sim list` | the scenarios: what each one simulates |
| `sim run --scenario email` | run a scenario; its data goes to runs/email-s40/ |
| `sim about email` | what a scenario simulates, and its planted problem if it has one |
| `xp analyse` | the difference B − A of the last run, its 95% interval and p-value (--metric) |
| `xp naive launch` | the naive answers to distrust: before against after, users against non-users |
| `xp check` | compare your last analysis with the true effect that the simulator knows (xp check RUN for another run) |
| `xp reset` | delete all runs and start again |
| `xp power --baseline 0.09 --mde 0.01 --per-day 4000` | sample size, power and duration (--simulate 200 checks the formula by simulation) |
| `xp plan new reminder-email` | write a test plan before the test; xp plan check FILE checks it |
| `xp analyse --bootstrap 1000` | a bootstrap interval |
| `xp analyse --cuped` | less noise with each customer's spending before the test |
| `xp analyse --by device` | the effect in each segment |
| `xp srm` | check the split for a sample ratio mismatch (--by device to find where it breaks) |
| `sim run --scenario aa` | an A/A test; sim run --scenario srm: a test with a redirect bug |
| `xp peek --aa-tests 1000` | how often daily peeking finds a false winner, and a sequential test |
| `xp peek early-stop` | a test day by day, with the sequential test's interval |
| `xp metrics many-metrics` | 20 metrics with Bonferroni and Benjamini-Hochberg |
| `xp weekly novelty` | the effect by week and by week since the first visit |
| `sim run --scenario stock` | shared stock (interference); also session and switchback |
| `xp did --placebo` | difference-in-differences on the regions run (--control all) |
| `xp synth` | a synthetic Quebec and placebo tests |
| `xp rdd --donut 40` | regression discontinuity at the Gold tier's 500 dollars |
| `xp its` | interrupted time series around the recommendation block's launch |
| `xp adjust` | regression, matching and weighting on the logs run, with a balance check |
| `xp refute` | DoWhy refutation tests and a hidden-confounder grid |

Every command has `--help`. Runs go to `runs/` (set `LARKFIELD_RUNS` to use another folder).

## Licence

MIT (see `LICENSE`).
