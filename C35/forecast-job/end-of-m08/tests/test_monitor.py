import pandas as pd

from forecast_job import monitor
from forecast_job.__main__ import main

from .conftest import START, make_data


def replay(data_dir, store, start, weeks):
    main(["replay", "--start", str(start.date()), "--weeks", str(weeks), "--data", str(data_dir),
          "--store", str(store)])


def test_no_alarm_on_normal_weeks(data_dir, tmp_path, capsys):
    replay(data_dir, tmp_path / "runs", START + pd.Timedelta(weeks=12), 4)
    assert "0 bias alarms, 0 weeks stopped" in capsys.readouterr().out


def test_the_alarm_fires_when_a_season_starts_early(tmp_path, capsys):
    jump = START + pd.Timedelta(weeks=13)
    data = make_data(tmp_path / "data", garden_jump=1.5, jump_from=jump)
    replay(data, tmp_path / "runs", START + pd.Timedelta(weeks=13), 4)
    out = capsys.readouterr().out
    assert "BIAS ALARM garden-furniture" in out and "too low" in out
    assert "BIAS ALARM kitchen" not in out


def test_one_bad_week_is_not_an_alarm(tmp_path):
    store = tmp_path / "runs"
    week = START + pd.Timedelta(weeks=12)
    for k, bias in enumerate([-35.0, 5.0]):
        d = store / str((week + pd.Timedelta(weeks=k)).date())
        d.mkdir(parents=True)
        pd.DataFrame([{"week": "", "category": "garden-furniture", "forecast": 1, "sales": 500,
                       "bias_pct": bias}]).to_csv(d / "check.csv", index=False)
    assert monitor.alarms(store, week + pd.Timedelta(weeks=1)) == []
