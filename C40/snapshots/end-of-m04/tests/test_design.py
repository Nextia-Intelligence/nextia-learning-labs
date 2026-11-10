"""Module 2: sample size, power and the test plan."""

import pytest

from larkfield_experiments import xp_cli
from larkfield_experiments.power import power_of, sample_size


def test_sample_size_gives_the_power():
    n = sample_size(0.09, 0.01)
    assert 13_000 < n < 14_000
    assert abs(power_of(n, 0.09, 0.01) - 0.8) < 0.01


def test_simulated_power_is_close_to_the_formula(capsys):
    xp_cli.main(["power", "--baseline", "0.09", "--mde", "0.01", "--simulate", "300"])
    line = [x for x in capsys.readouterr().out.splitlines() if "Simulated" in x][0]
    share = int(line.split("%")[0].split()[-1])
    assert 72 <= share <= 88


def test_plan_must_be_filled(capsys):
    xp_cli.main(["plan", "new", "email"])
    with pytest.raises(SystemExit):
        xp_cli.main(["plan", "check", "plans/email.md"])
    text = open("plans/email.md").read().replace("TODO", "filled")
    open("plans/email.md", "w").write(text)
    xp_cli.main(["plan", "check", "plans/email.md"])
    assert "Ready" in capsys.readouterr().out
