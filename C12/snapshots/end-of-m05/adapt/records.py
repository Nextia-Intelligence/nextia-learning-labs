"""Training examples: one ticket, one answer, in the chat format the model was made for (Module 2).

Every example has the same three messages: the short instruction (answer.SYSTEM_PROMPT), the ticket, and
the answer written by answer.format_answer. One format, so the model learns the task, not our typing
habits. Each record also says where it comes from.
"""

import csv
import tomllib
from pathlib import Path

from .answer import SYSTEM_PROMPT, format_answer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/source"


def messages(text: str, team: str | None = None, needs_human: bool | None = None) -> list[dict]:
    out = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]
    if team is not None:
        out.append({"role": "assistant", "content": format_answer(team, needs_human)})
    return out


def sources(root: Path = ROOT) -> dict:
    return tomllib.loads((root / "data/sources.toml").read_text(encoding="utf-8"))["sources"]


def load_source(folder: Path = SOURCE) -> list[dict]:
    """The training tickets joined with their needs_human labels."""
    with open(folder / "needs_human.csv", encoding="utf-8", newline="") as f:
        labels = {r["ticket_id"]: r for r in csv.DictReader(f)}
    with open(folder / "tickets.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        lab = labels[r["ticket_id"]]
        out.append({"id": r["ticket_id"], "text": r["text"], "team": r["team"], "style": r["style"],
                    "needs_human": lab["needs_human"] == "true", "rule": lab["rule"], "label_how": lab["how"],
                    "source": "tickets"})
    return out


def to_record(row: dict) -> dict:
    return {
        "id": row["id"],
        "messages": messages(row["text"], row["team"], row["needs_human"]),
        "team": row["team"],
        "needs_human": row["needs_human"],
        "style": row.get("style", ""),
        "source": row["source"],
        "label_how": row.get("label_how", ""),
    }
