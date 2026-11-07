"""The forecast note for a manager: the numbers of one week's plan, and a check that a drafted note uses
only those numbers.

An LLM can write the sentences of the note. It must not make up the numbers: check_note() finds every
number in the text and reports the ones that are not in the plan. The course's drafts were recorded once
(planner/notes_recorded.json); this project makes no model calls.
"""

import json
import re
from pathlib import Path

import pandas as pd

from .store import week_dir

NUMBER = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?%?")


def numbers(store, week):
    """The facts of the week that a note may quote."""
    d = week_dir(store, week)
    meta = json.loads((d / "run.json").read_text())
    orders = pd.read_csv(d / "orders.csv")
    by_cat = orders.groupby("category")["order"].sum().sort_values(ascending=False)
    top = orders.groupby(["product_id", "name"])["order"].sum().sort_values(ascending=False).head(3)
    facts = {
        "week": meta["week"],
        **meta["summary"],
        "top_categories": {k: int(v) for k, v in by_cat.head(3).items()},
        "top_products": {f"{pid} {name}": int(v) for (pid, name), v in top.items()},
        "warnings": [x[len("warning: "):] for x in (d / "checks.txt").read_text().splitlines()
                     if x.startswith("warning: ")],
        "alarms": _alarms_known(store, week),
    }
    if "override" in orders:
        facts["overrides"] = int(orders["override"].notna().sum())
    return facts


def _alarms_known(store, week):
    """The alarms known on the Monday: the ones raised by the check of the week before."""
    prev = week_dir(store, week - pd.Timedelta(weeks=1)) / "run.json"
    return json.loads(prev.read_text()).get("alarms", []) if prev.exists() else []


def _allowed(value, out):
    if isinstance(value, dict):
        for k, v in value.items():
            _allowed(k, out)
            _allowed(v, out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _allowed(v, out)
    elif isinstance(value, bool):
        pass
    elif isinstance(value, (int, float)):
        out.add(float(value))
    elif isinstance(value, str):
        for m in NUMBER.findall(value):
            out.add(_value(m))
    return out


def _value(text):
    return float(text.rstrip("%").replace(",", "").lstrip("+"))


def check_note(text, facts, tolerance=0.01):
    """Every number in the note that is not one of the facts (within 1%, so 4,213 may be written 4,200 only
    if 4,200 is a fact). Dates and product IDs count as facts too. Returns a list of the numbers that are
    not supported; an empty list means the note passed."""
    allowed = _allowed(facts, set())
    # small counting words that need no source (one week, two weeks, 14 days)
    allowed |= {1.0, 2.0, 7.0, 14.0}
    bad = []
    for m in NUMBER.findall(text):
        v = _value(m)
        if not any(abs(v - a) <= tolerance * max(abs(a), 1) for a in allowed):
            bad.append(m)
    return bad


def recorded(path, week):
    notes = json.loads(Path(path).read_text())
    for n in notes["notes"]:
        if n["week"] == str(week.date()):
            return n
    return None
