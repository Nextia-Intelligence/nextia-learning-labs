import numpy as np
import pandas as pd
import pytest

from forecast_job import config, plan


def test_the_cost_quantiles():
    assert config.STOCK_QUANTILE == pytest.approx(0.35 / 0.60)
    assert config.ROSTER_QUANTILE == pytest.approx(0.72)


def fake_forecast(mean=10.0, spread=4.0):
    days = pd.date_range("2025-03-10", periods=14, freq="D")
    return pd.DataFrame({"unique_id": "P001/north", "product_id": "P001", "region": "north", "ds": days,
                         "yhat": mean, "q10": mean - spread, "q90": mean + spread})


def test_the_order_is_above_the_forecast_when_a_lost_sale_costs_more():
    products = pd.DataFrame({"product_id": ["P001"], "name": ["Garden chair"], "category": ["garden-furniture"],
                             "base_price": [40.0]})
    o = plan.stock_orders(fake_forecast(), products)
    assert o.loc[0, "forecast"] == 140
    assert o.loc[0, "order"] > 140
    assert 0.38 < o.loc[0, "stock_out_chance"] < 0.42  # about 1 - 0.583, less after rounding the order up
    cheaper = plan.stock_orders(fake_forecast(), products, quantile=0.5)
    assert cheaper.loc[0, "order"] == 140


def test_roster_has_agents_only_in_open_hours():
    hours = pd.date_range("2025-03-10", periods=168, freq="h")
    t = pd.DataFrame({"ds": hours, "yhat": 13.0, "q10": 10.0, "q90": 16.0})
    r = plan.roster(t)
    open_ = r["hour"].dt.hour.isin(list(config.OPEN_HOURS))
    assert (r.loc[~open_, "agents"] == 0).all()
    assert (r.loc[open_, "agents"] == 3).all()  # 13 tickets + a bit, at 6 an hour
    assert np.isclose(r.loc[~open_, "expected_cost"], 0).all() and (r.loc[open_, "expected_cost"] > 0).all()
