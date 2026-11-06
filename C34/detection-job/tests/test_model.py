import pytest

from detect import model as model_mod
from detect.score import score_day


def test_train_save_load(payments, tmp_path):
    m = model_mod.train(payments, "2025-10-07", 60, history_days=10)
    assert m.rows > 1000
    model_mod.save(m, tmp_path / "state")
    again = model_mod.load(tmp_path / "state")
    assert again.version == m.version
    assert (tmp_path / "state" / "model.json").exists()


def test_the_stolen_card_scores_highest(payments):
    m = model_mod.train(payments, "2025-10-05", 60, history_days=10)
    sc = score_day(payments, "2025-10-06", m, history_days=60)
    assert sc.score.is_monotonic_decreasing
    assert sc.device_id.iloc[0] == "D-bad0001"
    assert (sc.head(10).device_id == "D-bad0001").sum() >= 7


def test_too_few_payments_is_a_clear_error(payments):
    with pytest.raises(SystemExit, match="too few"):
        model_mod.train(payments, "2025-08-03", 3, history_days=1)
