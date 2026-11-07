"""A small, made-up data folder for the tests: 3 products in 2 regions for 20 weeks, and hourly tickets."""

import numpy as np
import pandas as pd
import pytest

START = pd.Timestamp("2025-01-06")  # a Monday
DAYS = 140


def make_data(folder, days=DAYS, seed=1, garden_jump=1.0, jump_from=None):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(START, periods=days, freq="D")
    rows = []
    products = [("P001", "Garden chair, grey", "garden-furniture", 40.99, 20.0),
                ("P002", "Kettle, white", "kitchen", 34.99, 12.0),
                ("P003", "Rug, grey", "bedding-and-textiles", 89.99, 3.0)]
    for pid, _, cat, price, level in products:
        for region, share in (("north", 0.6), ("south", 0.4)):
            weekly = np.array([1.0, 0.9, 0.9, 1.0, 1.1, 1.3, 1.2])[dates.dayofweek]
            lam = level * share * weekly
            if cat == "garden-furniture" and jump_from is not None:
                weeks = np.clip((dates - jump_from).days // 7 + 1, 0, None)
                lam = lam * garden_jump ** weeks  # grows every week from jump_from
            sales = rng.poisson(lam)
            rows.append(pd.DataFrame({"date": dates, "region": region, "product_id": pid, "price": price,
                                      "on_promotion": 0, "sales": sales, "stock_out": 0}))
    demand = pd.concat(rows, ignore_index=True)
    hours = pd.date_range(START, periods=days * 24, freq="h")
    profile = np.where((hours.hour >= 8) & (hours.hour <= 20), 12.0, 1.0)
    tickets = pd.DataFrame({"timestamp": hours, "channel": "chat", "tickets": rng.poisson(profile)})
    folder.mkdir(parents=True, exist_ok=True)
    demand.to_csv(folder / "demand.csv.gz", index=False)
    tickets.to_csv(folder / "tickets_hourly.csv.gz", index=False)
    pd.DataFrame([{"product_id": p, "name": n, "category": c, "base_price": pr, "launch_date": "2025-01-06"}
                  for p, n, c, pr, _ in products]).to_csv(folder / "products.csv", index=False)
    pd.DataFrame(columns=["promotion_id", "product_id", "start", "end", "discount"]).to_csv(
        folder / "promotions.csv", index=False)
    pd.DataFrame(columns=["product_id", "date", "new_price", "reason"]).to_csv(
        folder / "price_changes.csv", index=False)
    return folder


@pytest.fixture
def data_dir(tmp_path):
    return make_data(tmp_path / "data")


@pytest.fixture
def week():
    return START + pd.Timedelta(weeks=12)
