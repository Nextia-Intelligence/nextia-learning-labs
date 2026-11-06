import pandas as pd

from forecast_job.__main__ import main


def test_one_run_writes_the_plan(data_dir, week, tmp_path, capsys):
    out = tmp_path / "plan"
    main(["run", "--week", str(week.date()), "--data", str(data_dir), "--out", str(out)])
    printed = capsys.readouterr().out
    assert "units to order" in printed
    for name in ("forecast.csv", "totals.csv", "orders.csv", "roster.csv"):
        assert (out / str(week.date()) / name).exists()
    orders = pd.read_csv(out / str(week.date()) / "orders.csv")
    assert len(orders) == 6
