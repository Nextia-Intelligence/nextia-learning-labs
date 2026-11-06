import pandas as pd

from forecast_job import config, model
from forecast_job.data import load


def test_stock_out_days_and_missing_days_are_filled(data_dir, week):
    inputs = load(data_dir, week)
    d = inputs.demand
    out_day = week - pd.Timedelta(days=3)
    row = (d["date"] == out_day) & (d["product_id"] == "P001") & (d["region"] == "north")
    d.loc[row, ["sales", "stock_out"]] = [0, 1]
    gap = week - pd.Timedelta(days=5)
    inputs.demand = d[d["date"] != gap]
    long = model.clean_series(inputs.demand)
    s = long[long["unique_id"] == "P001/north"].set_index("ds")["y"]
    assert gap in s.index
    assert s[out_day] == (s[out_day - pd.Timedelta(days=7)] + s[out_day - pd.Timedelta(days=14)]) / 2
    assert long["y"].notna().all()


def test_forecast_has_14_days_and_a_range(data_dir, week):
    fc = model.forecast_products(load(data_dir, week))
    assert fc.groupby("unique_id").size().eq(config.HORIZON_DAYS).all()
    assert fc["ds"].min() == week
    assert (fc["q10"] <= fc["yhat"]).all() and (fc["yhat"] <= fc["q90"]).all() and (fc["q5"] >= 0).all()


def test_totals_add_up(data_dir, week):
    inputs = load(data_dir, week)
    fc = model.forecast_products(inputs)
    totals = model.reconcile(fc, inputs.products)
    total = totals[totals["level"] == "total"]["yhat"].sum()
    by_region = totals[totals["level"] == "region"]["yhat"].sum()
    assert abs(total - fc["yhat"].sum()) < 0.1 and abs(by_region - total) < 0.1


def test_ticket_forecast_is_one_week_of_hours(data_dir, week):
    t = model.forecast_tickets(load(data_dir, week))
    assert len(t) == config.TICKET_HORIZON_HOURS and t["ds"].min() == week
