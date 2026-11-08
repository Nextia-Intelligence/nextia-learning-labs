"""Keyword rules and regular expressions (config/rules.json): the first rule that matches gives the route."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path | None = None) -> list[dict]:
    rules = json.loads((path or ROOT / "config" / "rules.json").read_text())["rules"]
    return [{**r, "regex": re.compile(r["pattern"], re.IGNORECASE)} for r in rules]


def match(text: str, rules: list[dict], strong_only: bool = False) -> dict | None:
    """The first rule that matches the text, or None."""
    for r in rules:
        if strong_only and not r.get("strong"):
            continue
        if r["regex"].search(text):
            return r
    return None
