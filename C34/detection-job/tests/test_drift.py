import numpy as np
import pandas as pd

from detect import drift


def test_psi_is_zero_for_the_same_data_and_large_for_a_shift():
    rng = np.random.default_rng(0)
    x = rng.normal(size=5000)
    assert drift.psi(x, x) < 0.001
    assert drift.psi(x, x + 1.0) > 0.25


def test_psi_of_a_yes_no_feature():
    assert drift.psi(np.r_[np.zeros(990), np.ones(10)], np.r_[np.zeros(700), np.ones(300)]) > 0.25


def test_verdict_asks_for_retraining_when_the_pressure_stays_high():
    table = pd.DataFrame({"feature": ["new_device", "amount"], "psi": [0.6, 0.01]})
    assert "Retrain" in drift.verdict(table, pd.Series([150, 160, 170]), 50)
    assert "no retraining" in drift.verdict(table, pd.Series([40, 30, 45]), 50)
    quiet = pd.DataFrame({"feature": ["amount"], "psi": [0.01]})
    assert drift.verdict(quiet, pd.Series([40, 30]), 50).startswith("No drift")
