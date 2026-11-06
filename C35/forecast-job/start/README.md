# Larkfield's forecasting job (start of Module 8)

A small command-line job that plans one week for Larkfield, the made-up online shop of the forecasting
course on [Nextia Learning](https://learning.nextia-ai.com/courses/forecasting/). It puts together what the
notebooks of Modules 2 to 7 did, for one Monday:

1. **gets the data** that was known on that Monday (the sales up to Sunday, the planned promotions and prices);
2. **checks it**, and stops if the data is not safe (a late feed, duplicated rows, negative sales);
3. **forecasts** every product in every region for 14 days, and the help-desk tickets per hour for one week,
   each with a range (exponential smoothing for the products, MSTL for the tickets);
4. **reconciles** the forecasts bottom-up, so that regions, categories and the total add up;
5. **writes the plan**: the stock order at the cost quantile and the help-desk roster, with their expected cost.

In Module 8 you make it a job that can run every week: it keeps every plan, watches its own error and records
the planners' changes.

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
python -m forecast_job run --week 2025-03-10      # plan one week (a Monday) into plan/2025-03-10/
```

## Files

| File | What it does |
|---|---|
| `forecast_job/config.py` | The horizon, the ranges and the costs (all assumptions) |
| `forecast_job/data.py` | Load what was known on the Monday, and check it |
| `forecast_job/model.py` | Clean the series (missing days, stock-outs), forecast products and tickets, reconcile |
| `forecast_job/plan.py` | The stock order and the roster from the forecast ranges, with their expected cost |

MIT licence (see `LICENSE`).
