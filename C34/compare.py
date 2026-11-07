"""The comparison table of the course Anomaly Detection: Find What Is Unusual.

Every module runs its detectors on the same Larkfield data and adds one row per detector to one table,
with the same columns and the same evaluation. This file scores a detector's output against the answer
key of the anomalies we planted, and prints the table.

    import compare
    table = compare.Table()
    table.add(compare.score_payments(payments, scores, "MAD per customer", "|robust z| on amount"))
    table.show()

The answer key is packed in data/sealed-key.txt, so that you do not read it by accident. This file unpacks
it to score your detector. You can unpack it yourself (compare.reveal()), but then you know the answers,
and your table no longer says how a detector does on data it has not seen.

Costs are assumptions of the course, the same in every lesson: a missed fraud payment costs its amount plus
a 15-dollar chargeback fee; a false alert costs about 3 dollars (4 minutes of the review team's time).
A blocked honest payment also costs a lost basket and some trust; the table counts these apart, with no
money value.

Needs pandas and NumPy only.
"""
import base64
import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

BUDGET = 50            # alerts a day that Sofia's team can review
CHARGEBACK_FEE = 15.0  # dollars, added to the amount of a missed fraud payment (assumption)
FALSE_ALERT_COST = 3.0  # dollars per false alert: 4 minutes of a reviewer (assumption)
# The same split in every module: detectors learn "normal" from the reference months and are scored on the
# evaluation months. The evaluation months have the new region, the product launch and Black Friday.
REFERENCE = ("2025-06-01", "2025-08-31")
EVALUATION = ("2025-09-01", "2025-11-30")
COLUMNS = ["detector", "setting", "alerts per day", "precision at budget", "recall", "cost per week ($)",
           "explain one alert (min)"]


def _find(name):
    here = Path(__file__).resolve().parent
    for p in (Path.cwd() / name, Path.cwd() / "data" / name, here / name, here / "data" / name):
        if p.exists():
            return p
    raise FileNotFoundError(f"{name} not found. Run the setup cell of the notebook first.")


_KEY = None


def _key():
    global _KEY
    if _KEY is None:
        _KEY = json.loads(zlib.decompress(base64.b64decode(_find("sealed-key.txt").read_text())))
    return _KEY


def reveal(table="payments"):
    """Unpack the answer key of one table. After this, you know the answers."""
    k = _key()[table]
    return pd.DataFrame(k) if isinstance(k, list) else k


def split(payments):
    """The payments of the reference months and of the evaluation months (the course's split)."""
    day = pd.to_datetime(payments.ts).dt.floor("D")
    ref = payments[(day >= REFERENCE[0]) & (day <= REFERENCE[1])]
    ev = payments[(day >= EVALUATION[0]) & (day <= EVALUATION[1])]
    return ref, ev


def planted_payments():
    """The planted fraud payments: payment_id, kind and episode (used by score_payments)."""
    return pd.DataFrame(_key()["payments"], columns=["payment_id", "kind", "episode"])


def _alerts_per_day(payments, scores, budget, threshold):
    p = payments[["payment_id", "ts", "amount"]].copy()
    p["score"] = np.asarray(scores, dtype=float)
    p["day"] = pd.to_datetime(p.ts).dt.floor("D")
    if threshold is None:
        p["alert"] = p.score.notna() & (p.score > -np.inf)
    else:
        p["alert"] = p.score >= threshold
    # Each day, the team reviews the alerts with the highest scores, at most `budget` of them. Ties keep
    # the time order (a rule gives every alert the same score: the first alerts of the day are reviewed).
    p = p.sort_values(["day", "score", "ts"], ascending=[True, False, True], kind="stable")
    p["rank"] = p[p.alert].groupby("day").cumcount()
    p["reviewed"] = p.alert & (p["rank"] < budget)
    if threshold is None:
        p["alert"] = p.reviewed      # top-k: the detector sends exactly the budget
    return p


def daily_alerts(payments, scores, budget=BUDGET, threshold=None):
    """One row per payment with its score, its day, `alert` and `reviewed` (the top `budget` alerts of each day)."""
    return _alerts_per_day(payments, scores, budget, threshold)


def score_payments(payments, scores, detector, setting="", budget=BUDGET, threshold=None, explain_minutes=None):
    """One row of the comparison table for a payments detector.

    payments: the payments table (or a part of it), with payment_id, ts and amount.
    scores:   one number per payment, in the same order; a higher score means "more unusual". For a rule,
              use 1 for a flagged payment and 0 for the others, and give threshold=1.
    threshold: None = every day, alert on the `budget` payments with the highest scores (top-k).
              A number = alert on every payment with a score at or above it; the team still reviews only
              `budget` a day, the highest scores first, and the other alerts wait (count them as missed).
    explain_minutes: how long a reviewer needs to understand one alert of this detector (an assumption:
              say where it comes from).
    """
    p = _alerts_per_day(payments, scores, budget, threshold)
    planted = planted_payments().set_index("payment_id")
    p["planted"] = p.payment_id.isin(planted.index)
    days = p.day.nunique()
    weeks = days / 7
    reviewed = p[p.reviewed]
    caught = reviewed.planted.sum()
    missed = p[p.planted & ~p.reviewed]
    false_alerts = (~reviewed.planted).sum()
    cost = (missed.amount.sum() + CHARGEBACK_FEE * len(missed) + FALSE_ALERT_COST * false_alerts) / weeks
    in_part = planted.loc[planted.index.isin(p.payment_id)]
    found_ep = planted.loc[reviewed[reviewed.planted].payment_id, "episode"].nunique()
    return {"detector": detector, "setting": setting,
            "alerts per day": round(p.alert.sum() / days, 1),
            "precision at budget": round(caught / len(reviewed), 3) if len(reviewed) else 0.0,
            "recall": round(caught / max(p.planted.sum(), 1), 3),
            "cost per week ($)": round(float(cost)),
            "explain one alert (min)": explain_minutes,
            # more detail, not printed in the short table
            "episodes found": f"{found_ep} of {in_part.episode.nunique()}",
            "false alerts per week": round(false_alerts / weeks, 1),
            "planted payments": int(p.planted.sum()), "days": int(days)}


def recall_by_kind(payments, scores, budget=BUDGET, threshold=None):
    """Recall of the planted payments per kind of fraud (stolen card, card testing, account takeover)."""
    p = _alerts_per_day(payments, scores, budget, threshold)
    pl = planted_payments().set_index("payment_id")
    p = p[p.payment_id.isin(pl.index)].copy()
    p["kind"] = p.payment_id.map(pl.kind)
    return p.groupby("kind").reviewed.mean().round(3)


def _events(times, flags, gap):
    """Join alerts that are less than `gap` apart into one alert event: [(start, end), ...]."""
    t = pd.to_datetime(pd.Series(times))[np.asarray(flags, dtype=bool)].sort_values()
    events, start, last = [], None, None
    for x in t:
        if start is None or x - last > gap:
            if start is not None:
                events.append((start, last))
            start = x
        last = x
    if start is not None:
        events.append((start, last))
    return events


def score_windows(times, flags, table, detector, setting="", gap="30min", explain_minutes=None, windows=None,
                  signal=None):
    """One row of the comparison table for a time-series detector.

    times, flags: one alert flag (True/False) per time step (minute, hour or day).
    table: "ticket_api" (the planted incidents in the ticket API metrics) or "orders" (the daily orders
           and tickets); or give your own windows: [{"name": ..., "start": ..., "end": ...}].
    signal: "latency" or "errors" to score a detector of one metric on the incidents of that metric only (an
           error alert during the memory leak is not a detection of the leak). None = every incident.
    Alerts less than `gap` apart are one alert event. A planted window is found when an event overlaps it;
    the time to detection is from the start of the window to the start of the first such event.
    """
    gap = pd.Timedelta(gap)
    if windows is None:
        windows = [w for w in _key()[table]["windows"] if w.get("anomaly", True)]
    if signal is not None:
        windows = [w for w in windows if w.get("signal") in (None, signal)]
    times = pd.to_datetime(pd.Series(times))
    span_days = (times.max() - times.min()) / pd.Timedelta("1D") + 1 / 1440
    ev = _events(times, flags, gap)
    found, delays, hit = 0, {}, set()
    for w in windows:
        a = pd.Timestamp(w["start"])
        b = pd.Timestamp(w["end"]) if w.get("end") else a + pd.Timedelta(w.get("detect_within", "1D"))
        firsts = []
        for i, (s, e) in enumerate(ev):
            if s <= b and e >= a:      # the alert event overlaps the window
                firsts.append(s)
                hit.add(i)
        if firsts:
            found += 1
            delays[w["name"]] = round(max((min(firsts) - a) / pd.Timedelta("1min"), 0))
        else:
            delays[w["name"]] = None
    false_events = len(ev) - len(hit)
    return {"detector": detector, "setting": setting,
            "alerts per day": round(len(ev) / span_days, 2),
            "precision at budget": round(len(hit) / len(ev), 3) if ev else 0.0,
            "recall": round(found / len(windows), 3),
            "cost per week ($)": round(FALSE_ALERT_COST * false_events / (span_days / 7)),
            "explain one alert (min)": explain_minutes,
            "minutes to detection": delays, "false alert events": false_events, "alert events": len(ev)}


def alarm_report(dates, alarms, shift_start, stable):
    """For a control chart: the first alarm on or after the shift, and the false alarms in a stable period.

    dates, alarms: one alarm flag per day. shift_start: the day the real shift starts.
    stable: (first day, last day) of a period with no planted change.
    """
    s = pd.DataFrame({"date": pd.to_datetime(pd.Series(dates)).to_numpy(), "alarm": np.asarray(alarms, bool)})
    after = s[(s.date >= pd.Timestamp(shift_start)) & s.alarm]
    first = after.date.min() if len(after) else None
    a, b = pd.Timestamp(stable[0]), pd.Timestamp(stable[1])
    st = s[(s.date >= a) & (s.date <= b)]
    months = ((b - a) / pd.Timedelta("1D") + 1) / 30.44
    return {"first alarm": None if first is None else str(first.date()),
            "days to alarm": None if first is None else int((first - pd.Timestamp(shift_start)).days),
            "false alarms per month": round(st.alarm.sum() / months, 2)}


class Table:
    """The comparison table: add rows, then show them."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def add(self, row):
        self.rows.append(row)
        return row

    def frame(self, columns=COLUMNS):
        return pd.DataFrame(self.rows)[columns]

    def show(self, columns=COLUMNS):
        with pd.option_context("display.max_columns", 20, "display.width", 160):
            print(self.frame(columns).to_string(index=False))
