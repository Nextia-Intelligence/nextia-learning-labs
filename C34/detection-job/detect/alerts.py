"""From scores to alerts: group the unusual payments, keep the budget, and say why each one is unusual."""
import hashlib

import pandas as pd

# The text of a reason, for a feature that is far above its usual value.
REASON_TEXT = {
    "log_amount_vs_usual": "amount {ratio:.1f} times the customer's usual amount",
    "new_country": "a country the customer never used before: {country}",
    "new_device": "a device the customer never used before",
    "log_minutes_since_last": "first payment after a long quiet time",
    "payments_last_hour": "{n:.0f} payments by the customer in one hour",
    "device_payments_last_hour": "{n:.0f} payments on this device in one hour",
    "night": "paid at night ({hour}:00)",
    "is_business": "a business account",
}
RUNBOOK = {
    "device_payments_last_hour": "Block the device for 24 hours, then check its other payments of today.",
    "new_device": "Ask the customer (app message or call) if they used a new device today.",
    "new_country": "Check if the customer is travelling (earlier payments, the delivery address).",
    "log_amount_vs_usual": "Compare the order with the customer's earlier orders and the delivery address.",
    "payments_last_hour": "Look at the customer's payments of the last hour together.",
}
DEFAULT_RUNBOOK = "Read the payments of the alert and the customer's last month."


def reasons(row, model, n=3):
    """The n features of a payment that are the most above their usual value (robust z), as text."""
    z = {f: (row[f] - model.median[f]) / model.spread[f] for f in model.median if f != "is_business"}
    out = []
    for f, v in sorted(z.items(), key=lambda kv: -kv[1])[:n]:
        if v <= 2:
            break
        out.append({"feature": f, "deviation": round(float(v), 1),
                    "text": REASON_TEXT[f].format(ratio=float(2.718281828 ** row["log_amount_vs_usual"]),
                                                  country=row["country"], n=float(row[f]), hour=int(row["hour"]))})
    return out


def alert_id(day, kind, key):
    """The same day and the same group always give the same ID, whatever the model: so a rerun of a day, even
    with a new model, never sends the same alert twice."""
    return hashlib.sha256(f"{day}|{kind}|{key}".encode()).hexdigest()[:16]


def group(scored, model, day, candidates=200):
    """Group the most unusual payments of a day: one alert per customer, or one per device when a device paid
    with the cards of 3 or more customers (card testing). Returns the alerts, the most unusual first."""
    top = scored.head(candidates)
    per_dev = top.groupby("device_id").customer_id.nunique()
    shared = set(per_dev[per_dev >= 3].index)
    top = top.assign(kind=["device" if d in shared else "customer" for d in top.device_id],
                     key=[d if d in shared else c for d, c in zip(top.device_id, top.customer_id, strict=True)])
    alerts = []
    for (kind, key), g in top.groupby(["kind", "key"], sort=False):
        best = g.iloc[0]
        rs = reasons(best, model)
        alerts.append({
            "alert_id": alert_id(day, kind, key), "day": str(day), "group": kind, "key": key,
            "customers": sorted(set(g.customer_id)), "payments": list(g.payment_id),
            "first": str(g.ts.min()), "last": str(g.ts.max()), "total_amount": round(float(g.amount.sum()), 2),
            "score": round(float(g.score.max()), 4), "reasons": rs,
            "runbook": RUNBOOK.get(rs[0]["feature"], DEFAULT_RUNBOOK) if rs else DEFAULT_RUNBOOK,
            "model": model.version})
    return sorted(alerts, key=lambda a: -a["score"])


def choose(alerts, policy, budget, fixed_threshold):
    """policy "budget": the `budget` most unusual alerts. policy "fixed": every alert above the threshold."""
    if policy == "budget":
        return alerts[:budget]
    if policy == "fixed":
        return [a for a in alerts if a["score"] >= fixed_threshold]
    raise SystemExit(f"Unknown policy {policy!r}: use budget or fixed.")


def above_threshold(scored: pd.DataFrame, fixed_threshold: float) -> int:
    """The pressure on the team: how many customers of the day have a payment above the training threshold.
    (The threshold was learned the same way: it gave `budget` customers a day in the training days.)"""
    return int(scored.loc[scored.score >= fixed_threshold, "customer_id"].nunique())
