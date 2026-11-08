import numpy as np

from larkvision import compare as cp


def test_iou_and_nms():
    assert cp.iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0
    assert round(cp.iou([0, 0, 10, 10], [5, 0, 10, 10]), 3) == 0.333
    keep = cp.nms([[0, 0, 10, 10], [1, 0, 10, 10], [50, 50, 10, 10]], [0.9, 0.8, 0.7], 0.5)
    assert keep == [0, 2]


def test_classification_scores_worst_class():
    s = cp.classification_scores(["a", "a", "b", "b"], ["a", "a", "a", "b"])
    assert s["accuracy"] == 0.75 and s["worst_class"] == "b" and s["worst_recall"] == 0.5


def test_lines_stay_inside_the_budget():
    rng = np.random.default_rng(0)
    scores = np.r_[rng.normal(0, 1, 540), rng.normal(3, 1, 60)]
    damaged = np.r_[np.zeros(540, bool), np.ones(60, bool)]
    lines = cp.choose_lines(scores, damaged)
    assert lines["checks_per_day"] <= 100
    none = cp.inspection_costs(scores, damaged, 1e9, 1e9)
    assert lines["cost_per_day"] < none["cost_per_day"] == 60 * 45


def test_auroc_and_count_scores():
    assert cp.roc_auc([0.1, 0.2, 0.9], [False, False, True]) == 1.0
    s = cp.count_scores([10, 20], [9, 25], ["loose", "tight"])
    assert s["mae"] == 3.0 and s["worst"] == "tight"
