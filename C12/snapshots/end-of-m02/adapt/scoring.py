"""Scores for the two decisions, the same measures as the evaluation course.

- answers: replies that are exactly one valid answer (answer.py)
- team: right team, over the cases that have a team
- needs a person: caught (said yes, and yes is right) and false alarms (said yes, no is right).
  No valid answer counts as "no": the ticket would not reach a person.
- decisions: the team (when the case has one) and needs_human both right
"""

import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    cases: int
    answers: int
    team_right: int
    team_cases: int
    caught: int
    needs_person: int
    false_alarms: int
    decisions: int
    median_seconds: float

    @property
    def decision_rate(self) -> float:
        return self.decisions / self.cases if self.cases else 0.0

    @property
    def team_accuracy(self) -> float:
        return self.team_right / self.team_cases if self.team_cases else 0.0

    @property
    def answer_rate(self) -> float:
        return self.answers / self.cases if self.cases else 0.0

    @property
    def recall(self) -> float:
        return self.caught / self.needs_person if self.needs_person else 1.0

    def line(self) -> str:
        return (f"answers {self.answers}/{self.cases} | team {self.team_right}/{self.team_cases} | "
                f"needs a person: caught {self.caught}/{self.needs_person}, false alarms {self.false_alarms} | "
                f"decisions {self.decisions}/{self.cases}")


def outcome(case, prediction) -> dict:
    """Right or wrong on each decision for one case (None: the case has no team to score)."""
    answer = prediction.answer if prediction else None
    said = bool(answer and answer["needs_human"])
    team_ok = None if not case.team else bool(answer and answer["team"] == case.team)
    human_ok = said == case.needs_human
    return {"answered": answer is not None, "team_ok": team_ok, "said_human": said,
            "human_ok": human_ok, "decision_ok": human_ok and team_ok is not False}


def score(cases, predictions) -> Score:
    rows = [outcome(c, predictions.get(c.case_id)) for c in cases]
    seconds = [predictions[c.case_id].seconds for c in cases if c.case_id in predictions]
    return Score(
        cases=len(cases),
        answers=sum(r["answered"] for r in rows),
        team_right=sum(r["team_ok"] is True for r in rows),
        team_cases=sum(r["team_ok"] is not None for r in rows),
        caught=sum(r["said_human"] and c.needs_human for c, r in zip(cases, rows)),
        needs_person=sum(c.needs_human for c in cases),
        false_alarms=sum(r["said_human"] and not c.needs_human for c, r in zip(cases, rows)),
        decisions=sum(r["decision_ok"] for r in rows),
        median_seconds=statistics.median(seconds) if seconds else 0.0,
    )


def by_slice(cases, predictions) -> dict[str, Score]:
    slices = sorted({c.slice for c in cases})
    return {s: score([c for c in cases if c.slice == s], predictions) for s in slices}
