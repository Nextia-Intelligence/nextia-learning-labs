"""A cascade: a cheap model decides when it is sure; the unsure messages go to a second step (an LLM, from its
recorded answers); what the second step is not sure about goes to a person (review)."""

import numpy as np
import pandas as pd

from larkroute import costs as cost_table


def run_cascade(first_proba: pd.DataFrame, second_route, second_conf, sure: float, second_sure: float) -> pd.DataFrame:
    """One row per message: the step that decided it and the route (or "review")."""
    p1 = first_proba.max(axis=1).to_numpy()
    r1 = first_proba.idxmax(axis=1).to_numpy()
    r2, c2 = np.asarray(second_route), np.asarray(second_conf, dtype=float)
    step = np.where(p1 >= sure, "first", np.where(c2 >= second_sure, "second", "person"))
    route = np.where(step == "first", r1, np.where(step == "second", r2, "review"))
    return pd.DataFrame({"step": step, "route": route}, index=first_proba.index)


def cost(truth: pd.DataFrame, result: pd.DataFrame, first_cost_per_msg: float, second_cost_per_msg: float,
         costs: dict) -> dict:
    """Cost per 1,000 messages: the mistakes, the reviews, and what each step costs to run."""
    n = len(truth)
    mistakes = cost_table.total(truth, result["route"], costs) / n * 1000
    second_share = (result["step"] != "first").mean()
    run = first_cost_per_msg * 1000 + second_cost_per_msg * 1000 * second_share
    decided = result["route"] != "review"
    share = result["step"].value_counts(normalize=True)
    return {"first": round(share.get("first", 0.0), 3), "second": round(share.get("second", 0.0), 3),
            "person": round(share.get("person", 0.0), 3),
            "accuracy_decided": round((result["route"][decided] == truth["route"][decided]).mean(), 3),
            "mistakes_and_reviews_per_1000": round(mistakes, 1), "run_per_1000": round(run, 3),
            "total_per_1000": round(mistakes + run, 1)}


GRID = np.round(np.arange(0.30, 1.0001, 0.05), 2)


def search(truth, first_proba, second_route, second_conf, first_cost, second_cost, costs,
           grid=GRID) -> tuple[float, float, dict]:
    """The pair of thresholds with the lowest total cost (use validation messages, never test)."""
    best = None
    for sure in grid:
        for second_sure in np.concatenate([[0.0], grid]):
            res = run_cascade(first_proba, second_route, second_conf, sure, second_sure)
            c = cost(truth, res, first_cost, second_cost, costs)
            if best is None or c["total_per_1000"] < best[2]["total_per_1000"]:
                best = (float(sure), float(second_sure), c)
    return best
