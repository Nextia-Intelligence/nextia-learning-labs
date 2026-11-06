import pandas as pd
import pytest

from forecast_job import overrides
from forecast_job.__main__ import main


def test_every_override_needs_a_reason(tmp_path):
    f = tmp_path / "o.csv"
    pd.DataFrame([{"week": "2025-03-10", "product_id": "P001", "region": "north", "order": 5, "reason": "",
                   "who": "Kenji"}]).to_csv(f, index=False)
    with pytest.raises(SystemExit, match="reason"):
        overrides.read(f)


def test_value_added_is_positive_when_the_override_was_closer(data_dir, week, tmp_path, capsys):
    store = tmp_path / "runs"
    main(["run", "--week", str(week.date()), "--data", str(data_dir), "--store", str(store)])
    sales = pd.read_csv(data_dir / "demand.csv.gz", parse_dates=["date"])
    days = pd.date_range(week, periods=14, freq="D")
    mine = sales["date"].isin(days) & (sales["product_id"] == "P002") & (sales["region"] == "south")
    sold = int(sales[mine]["sales"].sum())
    f = tmp_path / "o.csv"
    pd.DataFrame([{"week": str(week.date()), "product_id": "P002", "region": "south", "order": sold,
                   "reason": "knows the real sales", "who": "test"},
                  {"week": str(week.date()), "product_id": "P003", "region": "north", "order": 500,
                   "reason": "far too many", "who": "test"}]).to_csv(f, index=False)
    main(["run", "--week", str(week.date()), "--data", str(data_dir), "--store", str(store), "--overrides", str(f),
          "--force"])
    v = overrides.value_added(store, data_dir).set_index("reason")
    assert v.loc["knows the real sales", "fva_usd"] >= 0  # its order was exactly right
    assert v.loc["far too many", "fva_usd"] < 0
    capsys.readouterr()
    main(["fva", "--data", str(data_dir), "--store", str(store)])
    assert "Forecast value added" in capsys.readouterr().out
