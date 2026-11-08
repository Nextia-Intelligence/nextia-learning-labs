"""Score a method the same way every time: the columns of the course's comparison table."""

import pandas as pd
from sklearn.metrics import f1_score

from larkroute import costs as cost_table
from larkroute.data import ROUTES


def score(name: str, truth: pd.DataFrame, predicted, *, run_cost_per_1000: float = 0.0,
          ms_per_message: float | None = None, costs: dict | None = None) -> dict:
    """One row of the comparison table.

    truth: the messages (route, topic, priority, language), predicted: one route or "review" per message.
    run_cost_per_1000: what the method costs to run for 1,000 messages (computer time or tokens).
    """
    costs = costs or cost_table.load()
    pred = pd.Series(list(predicted), index=truth.index)
    right = pred == truth["route"]
    decided = pred != "review"
    ato = truth["topic"] == "account_takeover"
    person = truth["route"] == "needs_person"
    mistakes = cost_table.total(truth, pred, costs) / len(truth) * 1000
    return {
        "method": name,
        "accuracy": round(right.mean(), 3),
        "macro_f1": round(f1_score(truth["route"], pred, labels=ROUTES, average="macro", zero_division=0), 3),
        "takeover_recall": round((pred[ato] == "account").mean(), 3) if ato.any() else None,
        "needs_person_recall": round((pred[person] == "needs_person").mean(), 3) if person.any() else None,
        "accuracy_en": round(right[truth["language"] == "en"].mean(), 3),
        "accuracy_fr": round(right[truth["language"] == "fr"].mean(), 3),
        "review_share": round(1 - decided.mean(), 3),
        "mistakes_per_1000": round(mistakes, 1),
        "run_per_1000": round(run_cost_per_1000, 3),
        "total_per_1000": round(mistakes + run_cost_per_1000, 1),
        "ms_per_message": None if ms_per_message is None else round(ms_per_message, 2),
    }


def recall_by_route(truth: pd.DataFrame, predicted) -> pd.DataFrame:
    """Recall and the number of messages for each route (the rare routes need their counts next to them)."""
    pred = pd.Series(list(predicted), index=truth.index)
    rows = []
    for r in ROUTES:
        m = truth["route"] == r
        rows.append({"route": r, "messages": int(m.sum()), "recall": round((pred[m] == r).mean(), 3)})
    return pd.DataFrame(rows)


COLUMNS = {"method": "method", "accuracy": "accuracy", "macro_f1": "macro-F1", "takeover_recall": "takeover",
           "needs_person_recall": "needs person", "accuracy_en": "EN", "accuracy_fr": "FR",
           "mistakes_per_1000": "mistakes $/1k", "run_per_1000": "run $/1k", "total_per_1000": "total $/1k",
           "ms_per_message": "ms/msg"}


def table(rows: list[dict]) -> str:
    """The rows as a text table, cheapest total first."""
    df = pd.DataFrame(rows).sort_values("total_per_1000")
    show = df[[c for c in COLUMNS if c in df.columns]].rename(columns=COLUMNS)
    return show.to_string(index=False, na_rep="-")
