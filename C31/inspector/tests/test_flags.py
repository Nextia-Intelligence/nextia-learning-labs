"""The five flags on the saved data, against the scenario truth of each run (truth.json)."""

from conftest import truth

# truth.json scenario -> the flag that must fire on that run
EXPECTED = {"double_refund": "duplicate_write", "loop": "loop", "no_action": "no_action",
            "hidden_tool_error": "hidden_tool_error"}


def flagged(app, ds):
    return {r.run_id: set(r.flags) for r in app.sources[ds].runs.values()}


def test_every_scenario_run_has_its_flag(app):
    flags = flagged(app, "week")
    t = truth("week")
    checked = 0
    for run in t["runs"]:
        for scenario in run["scenarios"]:
            if scenario in EXPECTED:
                assert EXPECTED[scenario] in flags[run["run_id"]], (run["run_id"], scenario, flags[run["run_id"]])
                checked += 1
    assert checked == sum(1 for r in t["runs"] for s in r["scenarios"] if s in EXPECTED) > 0


def _expected_runs(name: str, scenario: str) -> set:
    return {r["run_id"] for r in truth(name)["runs"] if scenario in r["scenarios"]}


def test_duplicate_write(app):
    expected = _expected_runs("week", "double_refund")
    got = {rid for rid, f in flagged(app, "week").items() if "duplicate_write" in f}
    assert expected <= got
    # the flag also counts a return label written twice (truth counts refunds only): see the README
    for rid in got - expected:
        run = app.sources["week"].runs[rid]
        assert all(s.tool != "request_refund" for s in run.writes if s.get("larkfield.write.outcome") == "done")


def test_loop(app):
    expected = _expected_runs("week", "loop")
    got = {rid for rid, f in flagged(app, "week").items() if "loop" in f}
    assert expected <= got
    assert all(app.sources["week"].runs[r].model == "gemma3:4b" for r in got)


def test_no_action(app):
    expected = _expected_runs("week", "no_action")
    got = {rid for rid, f in flagged(app, "week").items() if "no_action" in f}
    assert expected <= got


def test_hidden_tool_error(app):
    expected = _expected_runs("week", "hidden_tool_error")
    got = {rid for rid, f in flagged(app, "week").items() if "hidden_tool_error" in f}
    assert expected <= got


def test_followed_injection_only_on_the_constructed_run(app):
    assert flagged(app, "constructed") == {"C-1016-001": {"followed_injection"}}
    assert not any("followed_injection" in f for f in flagged(app, "week").values())
    assert not any("followed_injection" in f for f in flagged(app, "healthy-week").values())


def test_healthy_week_has_no_flag(app):
    flags = flagged(app, "healthy-week")
    assert len(flags) == len(truth("healthy-week")["runs"])
    assert {rid: f for rid, f in flags.items() if f} == {}


def test_extra_flags_are_known(app):
    """Flags on runs that truth.json does not count as harmful (reported honestly in the README)."""
    t = {r["run_id"]: set(r["scenarios"]) for r in truth("week")["runs"]}
    extra = {(rid, name) for rid, f in flagged(app, "week").items() for name in f
             if not any(EXPECTED.get(s) == name for s in t.get(rid, ()))}
    print("flags on runs that truth.json does not count:", sorted(extra))
    # only the two rules that look at writes and errors may fire beyond the scenarios (a label written twice,
    # a second hidden error by the local model); the loop, no_action and injection flags never do
    assert {name for _, name in extra} <= {"duplicate_write", "hidden_tool_error"}, extra
