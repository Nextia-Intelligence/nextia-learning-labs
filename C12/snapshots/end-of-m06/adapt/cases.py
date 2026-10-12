"""The evaluation cases: the evaluation course's labelled tickets (data/eval/cases.jsonl).

dev is for choices (prompts, settings, checkpoints). holdout is for the final decision only: read it once,
at the end. contaminated holds the tickets that the hosted assistant's prompt was written on.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/eval/cases.jsonl"
SPLITS = ("dev", "holdout", "contaminated")


@dataclass(frozen=True)
class Case:
    case_id: str
    split: str
    slice: str
    language: str
    source: str
    style: str
    text: str
    attachments: str
    team: str          # "" when the ticket has no readable request
    needs_human: bool
    rule: str          # H1 ... H5, or ""
    critical: bool


def version(path: Path = CASES) -> str:
    """The first 12 hex digits of the file's SHA-256: one changed character gives a new version."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_cases(splits=("dev",), path: Path = CASES) -> list[Case]:
    for split in splits:
        if split not in SPLITS:
            raise ValueError(f"unknown split {split!r}; use one of {', '.join(SPLITS)}")
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["split"] in splits:
            out.append(Case(**row))
    return out


def model_input(case: Case) -> str:
    """The text that a model reads for one ticket: the message, and the attachment's name if there is one."""
    parts = [case.text.strip()] if case.text.strip() else []
    if case.attachments:
        parts.append(f"Attachment: {case.attachments}")
    return "\n\n".join(parts) if parts else "(empty message)"
