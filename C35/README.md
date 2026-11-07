# Forecasting and Time Series: Predict What Comes Next

Practice files for the course at [learning.nextia-ai.com/courses/forecasting/](https://learning.nextia-ai.com/courses/forecasting/).

| Path | What it is |
|---|---|
| `data/` | The Larkfield data: two years of daily sales for 200 products in 3 regions, orders, help-desk tickets per day and per hour, the roster, the weather, the calendar, promotions and price changes. Read [`data/dataset.md`](data/dataset.md). |
| `backtest.py` | The course's backtest helper: one rolling-origin backtest for any forecasting method, and the columns of the backtest table (MASE, WAPE, bias, pinball loss, fit time, cost). |
| `Mnn-Lnn-<slug>/` | The lesson notebooks, each with a solution notebook. Each one downloads what it needs, so you can open any lesson without the earlier ones. |
| `M09-L01-…`, `M09-L02-…`, `M09-L03-…` | The three case studies on real open data (bike-share rentals, electricity load, online retail), each with its notebook, solution and dataset card. The electricity folder also holds the 80-customer subset that its notebook downloads. |
| `forecast-job/start/` | The forecasting job at the start of Module 8: it plans one week into one folder. |
| `forecast-job/end-of-m08/` | The finished job: it keeps every plan, does nothing when you run the same week twice, raises a bias alarm, records overrides and checks a drafted note. |
| `final-assignment/data/` | The data of the final assignment: the same history with a new region and 40 new products. |

## Open a notebook

Open a lesson's notebook in Colab, Kaggle or VS Code and run it from the top. The first cells install the packages (pandas 2.3.3, statsforecast 2.1.1 and, where a lesson needs them, mlforecast 1.1.0, LightGBM 4.7.0, scikit-learn 1.9.1, hierarchicalforecast 1.5.3, and chronos-forecasting 2.3.2 with PyTorch 2.15.0 on the CPU), download the data and check its checksums. Every notebook runs on a laptop CPU in a few minutes.

## Run the forecasting job on your computer

Python 3.12. Copy one of the two folders of `forecast-job/` (start with `start/` in Module 8), then in that folder:

```sh
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python get_data.py
python -m pytest -q
python -m forecast_job run --week 2025-03-10
```

The `README.md` of each folder lists its commands.

The Larkfield data is synthetic: Larkfield, its products and its customers are made up, and there are no real people. The case studies use real open datasets; each `dataset.md` gives the source and the licence.
