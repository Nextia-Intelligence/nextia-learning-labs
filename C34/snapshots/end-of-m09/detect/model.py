"""Learn "normal" from a window of days, save it, and load it again.

The detector is Isolation Forest on the behaviour features (Module 4 of the course). The model file also
keeps what an alert needs to explain itself: the median and the spread of each feature in the training days.
"""
import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from . import data, features


@dataclass
class Model:
    version: str
    first_day: str
    last_day: str
    rows: int
    scaler: StandardScaler
    forest: IsolationForest
    median: dict
    spread: dict
    fixed_threshold: float      # the score that gave `budget` alerts a day in the training days ("fixed" policy)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """A higher score means more unusual."""
        return -self.forest.score_samples(self.scaler.transform(X[features.BEHAVIOUR]))


def behaviour_with_history(p: pd.DataFrame, first_day, last_day, history_days: int) -> pd.DataFrame:
    """Behaviour features of the payments from first_day to last_day. The features look back at the customer's
    earlier payments, so the window starts history_days earlier; those rows are dropped at the end."""
    start = pd.Timestamp(first_day) - pd.Timedelta(days=history_days)
    w = data.window(p, start, last_day).reset_index(drop=True)
    X = features.behaviour(w)
    keep = (w.ts >= pd.Timestamp(first_day)).to_numpy()
    return pd.concat([w[keep].reset_index(drop=True), X[keep].reset_index(drop=True)], axis=1)


def train(p: pd.DataFrame, last_day, days: int, history_days: int = 60, seed: int = 0, budget: int = 50) -> Model:
    first_day = (pd.Timestamp(last_day) - pd.Timedelta(days=days - 1)).date()
    f = behaviour_with_history(p, first_day, last_day, history_days)
    if len(f) < 1000:
        raise SystemExit(f"Only {len(f)} payments from {first_day} to {last_day}: too few to learn normal.")
    X = f[features.BEHAVIOUR]
    scaler = StandardScaler().fit(X)
    forest = IsolationForest(n_estimators=200, random_state=seed, n_jobs=-1).fit(scaler.transform(X))
    s = -forest.score_samples(scaler.transform(X))
    med = X.median()
    spread = (1.4826 * (X - med).abs().median()).where(lambda v: v > 0, X.std()).replace(0, 1.0)
    # the threshold that gave `budget` alerts a day (one per customer and day) on the training days
    best = pd.Series(s).groupby([f.ts.dt.floor("D").to_numpy(), f.customer_id.to_numpy()]).max().sort_values()
    n_days = f.ts.dt.floor("D").nunique()
    threshold = float(best.iloc[-min(budget * n_days, len(best))])
    return Model(version=f"iforest-{first_day}-{last_day}", first_day=str(first_day), last_day=str(last_day),
                 rows=len(f), scaler=scaler, forest=forest, median=med.round(6).to_dict(),
                 spread=spread.round(6).to_dict(), fixed_threshold=threshold)


def save(model: Model, state_dir: Path) -> Path:
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "model.pkl"
    path.write_bytes(pickle.dumps(model))
    info = {k: getattr(model, k) for k in ("version", "first_day", "last_day", "rows", "fixed_threshold")}
    (state_dir / "model.json").write_text(json.dumps(info, indent=1) + "\n")
    return path


def load(state_dir: Path) -> Model:
    path = Path(state_dir) / "model.pkl"
    if not path.exists():
        raise SystemExit("No model yet. Run: python -m detect train --until 2025-09-30")
    return pickle.loads(path.read_bytes())   # only a file this job wrote itself
