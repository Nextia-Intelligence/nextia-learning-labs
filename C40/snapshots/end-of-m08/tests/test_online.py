"""Module 8: the prompt test, bandits, the report and the test log."""

import numpy as np

from larkfield_experiments import xp_cli
from larkfield_experiments.bandit import run_bandit
from larkfield_experiments.commands.report import decide
from larkfield_experiments.runs import load_run
from larkfield_experiments.support import grade, load_answers


def test_grading_rules():
    base = {"id": "x", "prompt": "A", "category": "returns", "fact": "30", "tokens_in": 100, "tokens_out": 20}
    assert grade({**base, "must_hand_off": False, "answer": "You can return it within 30 days."})["correct"] == 1
    assert grade({**base, "must_hand_off": False, "answer": "I am connecting you with a support agent."})["correct"] == 0
    assert grade({**base, "must_hand_off": True, "answer": "Returns are free."})["unsafe"] == 1
    assert len(load_answers()) == 240


def test_prompt_test_finds_the_true_effect(make_run):
    make_run("prompt")
    xp_cli.main(["prompt"])
    a, truth = load_run("prompt").analysis(), load_run("prompt").truth()
    r = a["metrics"]["resolved"]
    assert r["low"] <= truth["resolved"]["effect"] <= r["high"]


def test_thompson_sends_traffic_to_the_best():
    last = [run_bandit([0.04, 0.046, 0.052, 0.044], 30_000, np.random.default_rng(s))[2][-1][2] for s in range(6)]
    assert np.mean(last) > 0.5  # one run can stay on a good-but-not-best line for a while


def test_report_decisions():
    assert decide({"low": 0.1, "high": 0.5}, {})[0] == "Ship B"
    assert decide({"low": -0.1, "high": 0.5}, {})[0].startswith("No clear effect")
    assert decide({"low": 0.1, "high": 0.5}, {"returns": {"low": 0.01}})[0] == "Discuss before shipping"


def test_log_add_and_stats(make_run, capsys):
    make_run("email", customers=5_000)
    xp_cli.main(["analyse"])
    xp_cli.main(["log", "add", "--decision", "ship", "--plan", "plans/email.md"])
    xp_cli.main(["log", "stats"])
    assert "1 tests: 1 shipped" in capsys.readouterr().out
