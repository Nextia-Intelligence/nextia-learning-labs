"""Methods whose answers the course recorded once: embedding models, the fine-tuned encoder, zero-shot models,
hosted and local LLMs. Their predictions for the validation and test messages are in data/predictions/
(one CSV and one JSON file per method), so you can compare them without a GPU, a download or a key.

The JSON file says how the answers were made ("measured" on a laptop CPU, or "recorded" from a hosted model),
the time per message and the cost to run 1,000 messages.
"""

import json

import pandas as pd

from larkroute.data import ROUTES, data_dir
from larkroute.methods import Method


def _files():
    folder = data_dir() / "predictions"
    return sorted(folder.glob("*.json")) if folder.exists() else []


class Recorded(Method):
    meta: dict = {}
    file = None

    def __init__(self):
        self.table = pd.read_csv(self.file.with_suffix(".csv")).set_index("message_id")

    def _rows(self, messages):
        missing = set(messages["message_id"]) - set(self.table.index)
        if missing:
            raise SystemExit(f"{self.name}: no recorded answer for {len(missing)} messages "
                             f"(recordings cover the validation and test messages)")
        return self.table.loc[messages["message_id"]]

    def predict(self, messages):
        return list(self._rows(messages)["prediction"])

    def confidence(self, messages):
        return self._rows(messages)["confidence"].to_numpy()

    def proba(self, messages):
        cols = [f"p_{r}" for r in ROUTES]
        rows = self._rows(messages)
        if not set(cols) <= set(rows.columns):
            raise NotImplementedError(f"{self.name} has no probabilities per route")
        return rows[cols].set_axis(ROUTES, axis=1).set_index(messages.index)

    def run_cost_per_1000(self, ms_per_message, compute):
        return self.meta["run_per_1000"]


def _make(path):
    meta = json.loads(path.read_text())
    return type(f"Recorded_{path.stem}", (Recorded,), {"name": meta["method"], "meta": meta, "file": path})


METHODS = {m.name: m for m in (_make(p) for p in _files())}


def ms_per_message(name: str) -> float | None:
    """The time per message that was measured when the answers were made (not the time to read the file)."""
    for p in _files():
        meta = json.loads(p.read_text())
        if meta["method"] == name:
            return meta.get("ms_per_message")
    return None
