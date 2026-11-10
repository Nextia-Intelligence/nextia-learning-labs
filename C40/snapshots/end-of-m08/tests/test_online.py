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


def test_log_add_and_stats(make_run, capsys, runs_in_tmp):
    (runs_in_tmp / "plans").mkdir()
    (runs_in_tmp / "plans" / "email.md").write_text("# Test plan: email\n")
    make_run("email", customers=5_000)
    xp_cli.main(["analyse"])
    xp_cli.main(["log", "add", "--decision", "ship", "--plan", "plans/email.md"])
    xp_cli.main(["srm"])
    xp_cli.main(["log", "add", "--decision", "Ship B"])
    xp_cli.main(["log", "add", "--decision", "do not ship"])
    xp_cli.main(["log", "stats"])
    out = capsys.readouterr().out
    assert "3 tests: 2 shipped" in out
    assert "logging the primary metric, ordered" in out


def test_log_add_needs_an_existing_plan(make_run):
    make_run("email", customers=2_000)
    xp_cli.main(["analyse"])
    try:
        xp_cli.main(["log", "add", "--decision", "ship", "--plan", "plans/missing.md"])
    except SystemExit as e:
        assert str(e).startswith("No plan file plans/missing.md")
    else:
        raise AssertionError("xp log add should stop when the plan file does not exist")


def test_report_works_on_the_prompt_test_and_reads_the_plan(make_run, runs_in_tmp):
    make_run("prompt")
    plan = runs_in_tmp / "plan.md"
    plan.write_text("- **Primary metric:** resolved\n- **Guardrail metrics:** complaint\n- **Duration:** 2 weeks\n")
    xp_cli.main(["report", "prompt", "--plan", str(plan)])
    text = (runs_in_tmp / "reports" / "prompt-s40.md").read_text()
    assert "- Duration: 14 days, 2025-10-20 to 2025-11-02, as in the plan." in text
    assert "- Primary metric: resolved, as in the plan." in text
    xp_cli.main(["report", "prompt"])
    assert "as in the plan" not in (runs_in_tmp / "reports" / "prompt-s40.md").read_text()
