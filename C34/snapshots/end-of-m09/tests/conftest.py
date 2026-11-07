"""A tiny payments table made in the test: 40 customers for 70 days, then one stolen card and one card test."""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

DAY0 = datetime(2025, 8, 1)


def make_payments(seed=0):
    rng = np.random.default_rng(seed)
    rows, n = [], 0
    for c in range(40):
        cust, dev = f"C-{c:05d}", f"D-{c:07x}"
        usual = float(rng.uniform(15, 120))
        for d in range(70):
            for _ in range(rng.poisson(0.5)):
                n += 1
                ts = DAY0 + timedelta(days=d, hours=int(rng.integers(8, 22)), minutes=int(rng.integers(0, 60)))
                rows.append((ts, cust, "personal", "north", round(usual * float(rng.uniform(0.7, 1.3)), 2), "CAD",
                             "CA", dev, "mobile", "garden"))
    # day 66: a stolen card, 8 payments in 10 minutes in Portugal on a new device, at 2 a.m.
    t = DAY0 + timedelta(days=66, hours=2, minutes=14)
    for k in range(8):
        rows.append((t + timedelta(minutes=k), "C-00007", "personal", "north", 20.0 + k, "EUR", "PT", "D-bad0001",
                     "mobile", "gift_cards"))
    # day 67: card testing, one device tries 5 customers' cards with tiny payments
    t = DAY0 + timedelta(days=67, hours=11)
    for k in range(5):
        rows.append((t + timedelta(minutes=k), f"C-{10 + k:05d}", "personal", "north", 1.5, "CAD", "CA", "D-test0001",
                     "desktop", "gift_cards"))
    p = pd.DataFrame(rows, columns=["ts", "customer_id", "account_type", "region", "amount", "currency", "country",
                                    "device_id", "device_type", "merchant_category"])
    p = p.sort_values("ts", kind="stable").reset_index(drop=True)
    p.insert(0, "payment_id", [f"P-{i:07d}" for i in range(1, len(p) + 1)])
    p["hour"] = p.ts.dt.hour
    return p


@pytest.fixture
def payments():
    return make_payments()


@pytest.fixture
def data_dir(tmp_path, payments):
    d = tmp_path / "data"
    d.mkdir()
    payments.to_csv(d / "payments.csv", index=False)
    return d
