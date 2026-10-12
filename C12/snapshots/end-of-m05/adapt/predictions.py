"""Saved predictions: one JSON line per case in runs/predictions/<system>.jsonl.

A prediction keeps the model's raw reply. The answer is parsed again every time it is loaded, with the one
strict check in answer.py, so every system is judged by the same rule.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .answer import parse_answer

ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "runs/predictions"


@dataclass(frozen=True)
class Prediction:
    case_id: str
    raw: str
    seconds: float
    answer: dict | None
    problem: str


def systems(folder: Path = PREDICTIONS) -> dict[str, dict]:
    """The saved systems and what each one is (runs/predictions/systems.json)."""
    return json.loads((folder / "systems.json").read_text(encoding="utf-8"))


def load_predictions(system: str, folder: Path = PREDICTIONS) -> dict[str, Prediction]:
    path = folder / f"{system}.jsonl"
    if not path.exists():
        known = ", ".join(sorted(p.stem for p in folder.glob("*.jsonl")))
        raise SystemExit(f"No saved predictions for {system!r}. Saved systems: {known}")
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        answer, problem = parse_answer(row["raw"])
        out[row["case_id"]] = Prediction(row["case_id"], row["raw"], row["seconds"], answer, problem)
    return out


def save_predictions(system: str, rows: list[dict], folder: Path = PREDICTIONS) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{system}.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                    encoding="utf-8")
    return path
