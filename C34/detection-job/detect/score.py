"""Score the payments of one day with the saved model."""
import pandas as pd

from . import model as model_mod


def score_day(p: pd.DataFrame, day, model, history_days: int = 60, features_frame=None) -> pd.DataFrame:
    """The day's payments with their behaviour features and their score, the most unusual first.
    features_frame: the features of a longer period, computed once (replay); else computed for the day."""
    if features_frame is None:
        f = model_mod.behaviour_with_history(p, day, day, history_days)
    else:
        d = pd.Timestamp(day)
        f = features_frame[(features_frame.ts >= d) & (features_frame.ts < d + pd.Timedelta("1D"))].copy()
    if f.empty:
        raise SystemExit(f"No payments on {day}.")
    f["score"] = model.score(f)
    return f.sort_values("score", ascending=False, kind="stable").reset_index(drop=True)
