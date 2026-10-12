"""Sort a system's mistakes into kinds before choosing a fix (Module 1).

Each kind points to a different fix. A format problem may need only a stricter output setting; a label
problem may need the labels in the prompt; a routing or person mistake is task behaviour. Missing knowledge
(a fact the model cannot know, such as today's delivery times) is the fourth kind; this task needs no such
fact, so it is not counted here.
"""

from .scoring import outcome

KINDS = {
    "format": "inconsistent format: no valid answer",
    "labels": "domain language: a team that Larkfield does not have",
    "routing": "task behaviour: valid answer, wrong team",
    "missed": "task behaviour: needs a person, not sent to one",
    "false_alarm": "task behaviour: sent to a person, no rule applies",
}


def kind_of(case, prediction) -> list[str]:
    """The kinds of mistake in one prediction ([] when both decisions are right)."""
    if prediction is None or prediction.answer is None:
        problem = prediction.problem if prediction else "no prediction"
        return ["labels" if problem == "unknown team" else "format"]
    o = outcome(case, prediction)
    kinds = []
    if o["team_ok"] is False:
        kinds.append("routing")
    if case.needs_human and not o["said_human"]:
        kinds.append("missed")
    if o["said_human"] and not case.needs_human:
        kinds.append("false_alarm")
    return kinds


def failures(cases, predictions) -> dict[str, list]:
    out = {k: [] for k in KINDS}
    for case in cases:
        for kind in kind_of(case, predictions.get(case.case_id)):
            out[kind].append(case)
    return out
