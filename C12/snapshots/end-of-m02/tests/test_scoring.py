from adapt.cases import load_cases
from adapt.predictions import load_predictions
from adapt.scoring import score
from adapt.targets import check, load_targets


def test_the_hosted_baseline_scores_as_in_the_evaluation_course():
    s = score(load_cases(), load_predictions("chat-small"))
    assert s.line() == ("answers 101/102 | team 97/100 | needs a person: caught 23/23, false alarms 9 | "
                        "decisions 90/102")


def test_no_answer_means_the_ticket_does_not_reach_a_person():
    cases = [c for c in load_cases() if c.needs_human][:3]
    s = score(cases, {})
    assert (s.answers, s.caught, s.needs_person, s.decisions) == (0, 0, 3, 0)


def test_targets_are_checked_one_by_one():
    s = score(load_cases(), load_predictions("chat-small"))
    rows = {name: met for name, _, _, met in check(s, load_targets())}
    assert rows["team"] and rows["needs a person caught"] and rows["decisions"]
    assert not rows["median seconds per answer"]  # the hosted model takes about 3 s per ticket
