"""The metrics of a test, computed per customer from a run's customers table."""

import pandas as pd

RATIOS = {"return_rate": ("returns", "orders"), "order_value": ("revenue", "orders")}


def metric_values(df: pd.DataFrame, metric: str) -> pd.Series:
    """The per-customer values of a metric (a mean metric): a column, or 'converted' (1 if they ordered)."""
    if metric == "converted":
        return (df["orders"] > 0).astype(int)
    if metric not in df.columns:
        raise SystemExit(f"No metric '{metric}'. Use one of: converted, {', '.join(RATIOS)}, or a column: "
                         f"{', '.join(c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]))}")
    return df[metric]


def split(df: pd.DataFrame):
    if set(df["variant"].unique()) - {"A", "B"}:
        raise SystemExit("This run is not an A/B test (no variant A and B).")
    return df[df["variant"] == "A"], df[df["variant"] == "B"]
