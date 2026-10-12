"""Check a system's scores against the targets in targets.toml (written before any training)."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ROOT / "targets.toml"


def load_targets(path: Path = TARGETS) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def check(score, targets: dict) -> list[tuple[str, str, str, bool]]:
    """(name, target, measured, met) for every target."""
    q, ops = targets["quality"], targets["operations"]
    rows = [
        ("answers", f">= {q['answers_min']:.2f}", f"{score.answer_rate:.2f}", score.answer_rate >= q["answers_min"]),
        ("team", f">= {q['team_min']:.2f}", f"{score.team_accuracy:.2f}", score.team_accuracy >= q["team_min"]),
        ("needs a person caught", f">= {q['needs_person_recall_min']:.2f}", f"{score.recall:.2f}",
         score.recall >= q["needs_person_recall_min"]),
        ("false alarms", f"<= {q['false_alarms_max']}", str(score.false_alarms),
         score.false_alarms <= q["false_alarms_max"]),
        ("decisions", f">= {q['decisions_min']:.2f}", f"{score.decision_rate:.2f}",
         score.decision_rate >= q["decisions_min"]),
        ("median seconds per answer", f"<= {ops['median_seconds_max']}", f"{score.median_seconds:.2f}",
         score.median_seconds <= ops["median_seconds_max"]),
    ]
    return rows
