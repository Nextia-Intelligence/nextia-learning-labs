"""The routing methods that `route compare` knows.

Each module in this folder has a METHODS dictionary: a name and a function that makes the method. A method
has `fit(train)` (a table of messages with their route) and `predict(messages)` (one route or "review" per
message); a method that gives probabilities also has `proba(messages)` (a table with one column per route).
A new module with a METHODS dictionary is found without any other change.
"""

import importlib
import pkgutil
import time

import pandas as pd

from larkroute.data import ROUTES


class Method:
    name = "method"
    trains = False  # True: fit() learns from the training messages

    def fit(self, train: pd.DataFrame) -> "Method":
        return self

    def predict(self, messages: pd.DataFrame) -> list[str]:
        p = self.proba(messages)
        return list(p.idxmax(axis=1))

    def proba(self, messages: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError(f"{self.name} gives no probabilities")

    def run_cost_per_1000(self, ms_per_message: float, compute: dict) -> float:
        """The cost of 1,000 messages: the computer time at the course's price (config/compute.json)."""
        return ms_per_message * 1000 / 1000 / 3600 * compute["usd_per_cpu_hour"]


def available() -> dict:
    found = {}
    for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{__name__}.{m.name}")
        found.update(getattr(mod, "METHODS", {}))
    for name, make in list(found.items()):
        if hasattr(make, "available") and not make.available():
            del found[name]
    return found


def timed_predict(method: Method, messages: pd.DataFrame) -> tuple[list[str], float]:
    """The predictions and the milliseconds per message."""
    t0 = time.perf_counter()
    pred = method.predict(messages)
    return pred, (time.perf_counter() - t0) * 1000 / max(len(messages), 1)


def as_proba(scores, classes) -> pd.DataFrame:
    df = pd.DataFrame(scores, columns=list(classes))
    for r in ROUTES:
        if r not in df:
            df[r] = 0.0
    return df[[r for r in ROUTES if r in df] + [c for c in df.columns if c not in ROUTES]]
