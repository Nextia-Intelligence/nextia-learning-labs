import filecmp

import pandas as pd
import pytest

from forecast_job.__main__ import main


def run(data_dir, store, week, *extra):
    main(["run", "--week", str(week.date()), "--data", str(data_dir), "--store", str(store), *extra])


def test_one_run_writes_the_plan(data_dir, week, tmp_path, capsys):
    run(data_dir, tmp_path / "runs", week)
    assert "units to order" in capsys.readouterr().out
    d = tmp_path / "runs" / str(week.date())
    for name in ("forecast.csv", "totals.csv", "orders.csv", "roster.csv", "checks.txt", "run.json"):
        assert (d / name).exists()
    assert len(pd.read_csv(d / "orders.csv")) == 6


def test_a_second_run_with_the_same_inputs_changes_nothing(data_dir, week, tmp_path, capsys):
    run(data_dir, tmp_path / "a", week)
    run(data_dir, tmp_path / "b", week)
    a, b = tmp_path / "a" / str(week.date()), tmp_path / "b" / str(week.date())
    names = ["forecast.csv", "orders.csv", "roster.csv", "run.json"]
    assert filecmp.cmpfiles(a, b, names, shallow=False)[0] == names
    capsys.readouterr()
    run(data_dir, tmp_path / "a", week)
    assert "Nothing to do" in capsys.readouterr().out


def test_other_inputs_need_force_and_keep_the_old_plan(data_dir, week, tmp_path):
    run(data_dir, tmp_path / "runs", week)
    over = tmp_path / "overrides.csv"
    pd.DataFrame([{"week": str(week.date()), "product_id": "P001", "region": "north", "order": 99,
                   "reason": "promotion next week", "who": "Kenji"}]).to_csv(over, index=False)
    with pytest.raises(Exception, match="--force"):
        run(data_dir, tmp_path / "runs", week, "--overrides", str(over))
    run(data_dir, tmp_path / "runs", week, "--overrides", str(over), "--force")
    d = tmp_path / "runs" / str(week.date())
    assert list(d.glob("replaced-*/orders.csv"))
    orders = pd.read_csv(d / "orders.csv")
    row = orders[(orders["product_id"] == "P001") & (orders["region"] == "north")].iloc[0]
    assert row["order"] == 99 and row["reason"] == "promotion next week" and row["job_order"] != 99


def test_bad_data_stops_and_writes_nothing(data_dir, week, tmp_path, capsys):
    late = week + pd.Timedelta(weeks=30)
    with pytest.raises(SystemExit):
        run(data_dir, tmp_path / "runs", late)
    assert "STOPPED" in capsys.readouterr().out
    assert not (tmp_path / "runs" / str(late.date())).exists()
