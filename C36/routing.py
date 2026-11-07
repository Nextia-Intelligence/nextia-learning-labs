"""Helpers for the text routing course's notebooks: the cost table, the comparison table's columns, and the
reliability table. The same rules as the course project (`larkroute`), in one file.

    import routing as rt
    rt.score("my method", test, predictions)       one row of the comparison table
    rt.show([row1, row2])                          the rows as a table, cheapest first

A prediction is a route or "review" (a person reads the message first). The data is synthetic.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROUTES = ["orders", "delivery", "returns_refunds", "billing", "product", "account", "needs_person"]
# The cost of each kind of mistake in US dollars (assumptions agreed for the course; data/costs.json says why).
COSTS = {"review": 1.5, "wrong_queue": 4.0, "wrong_queue_urgent": 20.0, "missed_account_takeover": 200.0,
         "needs_person_sent_to_team": 40.0, "team_message_sent_to_person": 2.0}


def load_costs(path="data/costs.json"):
    p = Path(path)
    return {k: v for k, v in json.loads(p.read_text()).items() if isinstance(v, (int, float))} if p.exists() else COSTS


def message_cost(true_route, predicted, priority, topic, costs=COSTS):
    """The cost of one routing decision."""
    if predicted == true_route:
        return 0.0
    if predicted == "review":
        return costs["review"]
    if predicted == "needs_person":
        return costs["team_message_sent_to_person"]
    if topic == "account_takeover":
        return costs["missed_account_takeover"]
    if true_route == "needs_person":
        return costs["needs_person_sent_to_team"]
    return costs["wrong_queue_urgent"] if priority == "urgent" else costs["wrong_queue"]


def cost_per_1000(truth, predicted, costs=COSTS):
    total = sum(message_cost(t, p, pr, tp, costs) for t, p, pr, tp in
                zip(truth["route"], predicted, truth["priority"], truth["topic"], strict=True))
    return total / len(truth) * 1000


def macro_f1(truth, pred):
    f1s = []
    for r in ROUTES:
        tp = ((pred == r) & (truth == r)).sum()
        fp = ((pred == r) & (truth != r)).sum()
        fn = ((pred != r) & (truth == r)).sum()
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f1s))


def score(name, truth, predicted, run_per_1000=0.0, ms_per_message=None, costs=COSTS):
    """One row of the comparison table (the same columns as `route compare`)."""
    pred = pd.Series(list(predicted), index=truth.index)
    right = pred == truth["route"]
    ato, person = truth["topic"] == "account_takeover", truth["route"] == "needs_person"
    mistakes = cost_per_1000(truth, pred, costs)
    return {"method": name, "accuracy": round(right.mean(), 3), "macro_f1": round(macro_f1(truth["route"], pred), 3),
            "takeover_recall": round((pred[ato] == "account").mean(), 3) if ato.any() else None,
            "needs_person_recall": round((pred[person] == "needs_person").mean(), 3) if person.any() else None,
            "accuracy_en": round(right[truth["language"] == "en"].mean(), 3),
            "accuracy_fr": round(right[truth["language"] == "fr"].mean(), 3),
            "review_share": round((pred == "review").mean(), 3),
            "mistakes_per_1000": round(mistakes, 1), "run_per_1000": round(run_per_1000, 3),
            "total_per_1000": round(mistakes + run_per_1000, 1),
            "ms_per_message": None if ms_per_message is None else round(ms_per_message, 2)}


def show(rows):
    """The rows as a table, cheapest total first."""
    cols = ["method", "accuracy", "macro_f1", "takeover_recall", "needs_person_recall", "accuracy_en", "accuracy_fr",
            "mistakes_per_1000", "run_per_1000", "total_per_1000", "ms_per_message"]
    df = pd.DataFrame(rows).sort_values("total_per_1000")
    return df[[c for c in cols if c in df.columns]].reset_index(drop=True)


def reliability(confidence, correct, bins=10):
    """The reliability table (mean confidence and accuracy per bin) and the expected calibration error."""
    conf, ok = np.asarray(confidence, float), np.asarray(correct, bool)
    edges = np.linspace(0, 1, bins + 1)
    rows, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        m = (conf >= lo) & ((conf < hi) | (hi == 1.0))
        if m.any():
            rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "messages": int(m.sum()),
                         "mean_confidence": round(conf[m].mean(), 3), "accuracy": round(ok[m].mean(), 3)})
            ece += m.mean() * abs(conf[m].mean() - ok[m].mean())
    return pd.DataFrame(rows), round(float(ece), 4)


def predictions(slug, messages, folder="data/predictions"):
    """A recorded or measured method's predictions for these messages (validation or test)."""
    df = pd.read_csv(Path(folder) / f"{slug}.csv").set_index("message_id")
    meta = json.loads((Path(folder) / f"{slug}.json").read_text())
    return df.loc[messages["message_id"]].reset_index(), meta
