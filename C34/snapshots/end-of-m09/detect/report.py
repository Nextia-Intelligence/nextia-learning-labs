"""The weekly alert report: what was sent, what was snoozed, what the reviewers said, what nobody read."""
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from .suppress import reviews


def _read(path: Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def weekly(state_dir: Path, alerts_dir: Path, last_day, unread_after_days: int = 2) -> str:
    last = pd.Timestamp(last_day)
    days = [(last - pd.Timedelta(days=k)).date() for k in range(6, -1, -1)]
    rv = reviews(state_dir).drop_duplicates("alert_id", keep="last").set_index("alert_id")
    snoozed = Counter(x["day"] for x in _read(Path(state_dir) / "snoozed.jsonl"))
    lines = [f"Alert report, week {days[0]} to {days[-1]}", "",
             f"{'day':<12}{'sent':>6}{'snoozed':>9}{'real':>6}{'not':>5}{'unread':>8}"]
    reasons, unread_old, total = Counter(), [], Counter()
    for d in days:
        sent = _read(Path(alerts_dir) / f"{d}.jsonl")
        lab = [rv.label.get(a["alert_id"]) for a in sent]
        real, not_, unread = lab.count("real"), lab.count("not"), lab.count(None)
        total.update(sent=len(sent), real=real, not_=not_, unread=unread, snoozed=snoozed[str(d)])
        lines.append(f"{str(d):<12}{len(sent):>6}{snoozed[str(d)]:>9}{real:>6}{not_:>5}{unread:>8}")
        for a in sent:
            if a["reasons"]:
                reasons[a["reasons"][0]["feature"]] += 1
            if rv.label.get(a["alert_id"]) is None and (last - pd.Timestamp(d)).days >= unread_after_days:
                unread_old.append(a["alert_id"])
    lines += [f"{'total':<12}{total['sent']:>6}{total['snoozed']:>9}{total['real']:>6}{total['not_']:>5}"
              f"{total['unread']:>8}", ""]
    reviewed = total["real"] + total["not_"]
    if reviewed:
        share = total["real"] / reviewed
        lines.append(f"Precision of the reviewed alerts: {share:.2f} ({total['real']} of {reviewed}).")
    lines.append("Main reason of the alerts: " + ", ".join(f"{k} {v}" for k, v in reasons.most_common(4)) + ".")
    lines.append(f"Alerts nobody read after {unread_after_days} days: {len(unread_old)}. "
                 "Ask why in the weekly review: too many alerts, or alerts that never lead to action?")
    return "\n".join(lines)
