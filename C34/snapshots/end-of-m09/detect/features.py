"""Behaviour features for the Larkfield payments (the same as the course's features.py).

The raw columns say little about fraud: a 20-dollar payment is normal. What makes a stolen card visible is
the payment compared with the customer's own past: a country or a device the customer never used, many
payments in one hour, an amount far above the customer's usual one.

    X = behaviour(payments)          # one row per payment, in the same order

Every feature uses only the payments BEFORE (or at) the payment's own time, as a live detector would.
Needs pandas and NumPy only.
"""
import numpy as np
import pandas as pd

RAW = ["amount", "hour", "is_business"]
BEHAVIOUR = ["log_amount_vs_usual", "new_country", "new_device", "log_minutes_since_last",
             "payments_last_hour", "device_payments_last_hour", "night", "is_business"]


def raw(payments):
    """The raw numbers of each payment: amount, hour and account type (1 = business)."""
    return pd.DataFrame({"amount": payments.amount.to_numpy(), "hour": payments.hour.to_numpy(),
                         "is_business": (payments.account_type == "business").astype(int).to_numpy()})


def behaviour(payments):
    """Features that compare each payment with the customer's own past (and the device's last hour)."""
    p = payments[["payment_id", "ts", "customer_id", "account_type", "amount", "country", "device_id",
                  "hour"]].copy()
    p["ts"] = pd.to_datetime(p.ts)
    p["_order"] = np.arange(len(p))
    p = p.sort_values(["ts", "_order"], kind="stable")
    g = p.groupby("customer_id", sort=False)
    # the customer's usual amount: the median of their last 10 payments before this one
    usual = g.amount.transform(lambda s: s.shift().rolling(10, min_periods=1).median())
    p["log_amount_vs_usual"] = np.log(p.amount / usual.fillna(p.amount))
    # a country (or device) that the customer never used before today; not for a customer's first day
    day = p.ts.dt.floor("D")
    first_day = g.ts.transform("min").dt.floor("D")
    for col, name in (("country", "new_country"), ("device_id", "new_device")):
        seen = p.groupby(["customer_id", col], sort=False).ts.transform("min").dt.floor("D")
        p[name] = ((seen == day) & (first_day < day)).astype(int)
    since = g.ts.diff().dt.total_seconds() / 60
    p["log_minutes_since_last"] = np.log1p(since.fillna(60 * 24 * 90))
    ones = pd.Series(1, index=p.index)
    p["payments_last_hour"] = (ones.groupby(p.customer_id).transform(
        lambda s: s.set_axis(p.loc[s.index, "ts"]).rolling("3600s").sum().to_numpy()))
    p["device_payments_last_hour"] = (ones.groupby(p.device_id).transform(
        lambda s: s.set_axis(p.loc[s.index, "ts"]).rolling("3600s").sum().to_numpy()))
    p["night"] = p.hour.between(0, 5).astype(int)
    p["is_business"] = (p.account_type == "business").astype(int)
    p = p.sort_values("_order")
    return p[BEHAVIOUR].reset_index(drop=True)
