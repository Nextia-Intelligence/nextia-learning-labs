# Larkfield's forecasting job

A small command-line job that plans one week for Larkfield, the made-up online shop of the forecasting
course on [Nextia Learning](https://learning.nextia-ai.com/courses/forecasting/). Every Monday it:

1. **gets the data** that was known on that Monday (the sales up to Sunday, the planned promotions and prices);
2. **checks it**, and stops if the data is not safe (a late feed, duplicated rows, negative sales);
3. **forecasts** every product in every region for 14 days, and the help-desk tickets per hour for one week,
   each with a range (exponential smoothing for the products, MSTL for the tickets);
4. **reconciles** the forecasts bottom-up, so that regions, categories and the total add up;
5. **writes the plan**: the stock order at the cost quantile and the help-desk roster, with their expected cost;
6. **keeps** every plan in `runs/<Monday>/`, and does nothing if you run the same week again with the same inputs.

It also compares each plan with what was sold a week later (a **bias alarm**), applies a planner's
**overrides** with their reason and measures whether they helped (**forecast value added**), and checks
that a drafted note for the manager uses only the plan's numbers.

The data is synthetic. It has no real people, products or prices.

## Set up

Python 3.12. In this folder:

```sh
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python get_data.py                   # about 2 MB into data/
python -m pytest -q
```

## Use

```sh
python -m forecast_job run --week 2025-03-10                    # plan one week (a Monday)
python -m forecast_job replay --start 2025-03-03 --weeks 12     # a quarter, week after week, with checks
python -m forecast_job check --week 2025-03-10                  # the plan's first week against the sales
python -m forecast_job fva                                      # did the overrides help?
python -m forecast_job note --week 2025-03-24                   # the numbers for the manager's note
```

`replay` uses `planner/overrides_replay.csv` (a planner's changes to some orders, a situation we planted).
Run every command from this folder. To start again, delete the folder `runs/`.

To run it every Monday at 06:00 on Linux or macOS, a cron line is enough (Windows: Task Scheduler):

```
0 6 * * 1  cd /path/to/forecast-job && .venv/bin/python -m forecast_job run --week "$(date +\%F)"
```

## Files

| File | What it does |
|---|---|
| `forecast_job/config.py` | The horizon, the ranges and the costs (all assumptions) |
| `forecast_job/data.py` | Load what was known on the Monday, and check it |
| `forecast_job/model.py` | Clean the series (missing days, stock-outs), forecast products and tickets, reconcile |
| `forecast_job/plan.py` | The stock order and the roster from the forecast ranges, with their expected cost |
| `forecast_job/store.py` | One folder per week, a fingerprint of the inputs, no double runs |
| `forecast_job/monitor.py` | The check of last week's plan and the bias alarm |
| `forecast_job/overrides.py` | Overrides with a reason, and forecast value added |
| `forecast_job/note.py` | The numbers of a plan, and the check of a drafted note |
| `planner/overrides_replay.csv` | The planner's overrides in the replayed quarter |
| `planner/notes_recorded.json` | Drafted notes for the manager, recorded once from a small LLM |

MIT licence (see `LICENSE`).
