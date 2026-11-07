from test_service import FakeInspector, no_faces

from larkvision import data as D
from larkvision.commands.replay import replay
from larkvision.drift import psi


def test_psi_is_small_for_the_same_scores_and_large_for_a_shift():
    a = [0.1 * i for i in range(100)]
    assert psi(a, a) < 0.01 and psi(a, [x + 5 for x in a]) > 1


def test_replay_writes_weeks_and_alarms(data, tmp_path):
    results, summary = replay(data, D.month(data), FakeInspector(), no_faces, tmp_path / "review", D.costs(data))
    assert len(results) == 8 and sum(s["photos"] for s in summary) == 8
    assert any(s["alarms"] for s in summary)  # the fake scores are far from the validation scores
