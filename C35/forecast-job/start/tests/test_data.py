import pandas as pd
import pytest

from forecast_job.data import DataError, check, load, monday


def test_load_keeps_only_what_was_known(data_dir, week):
    inputs = load(data_dir, week)
    assert inputs.demand["date"].max() == week - pd.Timedelta(days=1)
    assert inputs.tickets["timestamp"].max() == week - pd.Timedelta(hours=1)


def test_a_week_starts_on_a_monday():
    with pytest.raises(SystemExit):
        monday("2025-03-12")
    assert monday("2025-03-10").dayofweek == 0


def test_clean_data_has_no_warnings(data_dir, week):
    assert check(load(data_dir, week)) == []


def test_a_late_feed_stops_the_job(data_dir, week):
    inputs = load(data_dir, week)
    inputs.demand = inputs.demand[inputs.demand["date"] < week - pd.Timedelta(days=2)]
    with pytest.raises(DataError, match="late"):
        check(inputs)


def test_duplicates_and_negative_sales_stop_the_job(data_dir, week):
    inputs = load(data_dir, week)
    inputs.demand = pd.concat([inputs.demand, inputs.demand.tail(1)])
    with pytest.raises(DataError, match="duplicated"):
        check(inputs)
    inputs = load(data_dir, week)
    inputs.demand.loc[0, "sales"] = -1
    with pytest.raises(DataError, match="negative"):
        check(inputs)


def test_a_missing_day_and_many_stock_outs_are_warnings(data_dir, week):
    inputs = load(data_dir, week)
    gap = week - pd.Timedelta(days=10)
    inputs.demand = inputs.demand[inputs.demand["date"] != gap]
    recent = inputs.demand["date"] > week - pd.Timedelta(days=8)
    inputs.demand.loc[recent & (inputs.demand["product_id"] == "P001"), "stock_out"] = 1
    warnings = check(inputs)
    assert any(str(gap.date()) in w for w in warnings)
    assert any("stock-outs" in w for w in warnings)
