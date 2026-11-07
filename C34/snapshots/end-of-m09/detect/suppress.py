"""Reviews, and the snooze rule: after a reviewer marks a customer's alert "not fraud", that customer's
alerts wait for a few days (they would most likely be the same honest change again)."""
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def reviews(state_dir: Path) -> pd.DataFrame:
    path = Path(state_dir) / "reviews.jsonl"
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []
    return pd.DataFrame(rows, columns=["alert_id", "label", "day", "customers", "at"])


def add_review(state_dir: Path, alerts_dir: Path, alert_id: str, label: str):
    if label not in ("real", "not"):
        raise SystemExit("The label is real (fraud) or not (not fraud).")
    found = None
    for f in sorted(Path(alerts_dir).glob("*.jsonl")):
        for line in f.read_text().splitlines():
            a = json.loads(line)
            if a["alert_id"] == alert_id:
                found = a
    if found is None:
        raise SystemExit(f"No alert {alert_id} in {alerts_dir}/.")
    rec = {"alert_id": alert_id, "label": label, "day": found["day"], "customers": found["customers"],
           "at": datetime.now(UTC).isoformat(timespec="seconds")}
    with open(Path(state_dir) / "reviews.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def snoozed_customers(state_dir: Path, day, snooze_days: int) -> set:
    r = reviews(state_dir)
    if r.empty:
        return set()
    d = pd.Timestamp(day)
    day_of = pd.to_datetime(r.day)
    recent = r[(r.label == "not") & (day_of < d) & (day_of >= d - pd.Timedelta(days=snooze_days))]
    return {c for cs in recent.customers for c in cs}


def apply(alerts, snoozed: set):
    """Split the alerts into (kept, snoozed). A device alert (several customers) is never snoozed."""
    keep, held = [], []
    for a in alerts:
        (held if a["group"] == "customer" and a["key"] in snoozed else keep).append(a)
    return keep, held
