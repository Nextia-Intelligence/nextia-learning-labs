"""Check a folder of exported telemetry for data that must not leave the application.

It looks at every attribute of every span, span event and log record, and at log bodies:
- attribute names that carry text by the GenAI conventions (prompts, answers, tool arguments and results),
- e-mail addresses and card-like numbers (13 to 19 digits) in any value,
- long strings (more than 200 characters) that look like sentences.
"""

import re
from pathlib import Path

from .model import attributes, lines

TEXT_KEYS = {"gen_ai.input.messages", "gen_ai.output.messages", "gen_ai.system_instructions",
             "gen_ai.tool.call.arguments", "gen_ai.tool.call.result", "gen_ai.prompt", "gen_ai.completion"}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def problems_in(where: str, attrs: dict) -> list[str]:
    out = []
    for k, v in attrs.items():
        if k in TEXT_KEYS:
            out.append(f"{where}: attribute {k} (text)")
            continue
        text = v if isinstance(v, str) else ""
        if EMAIL.search(text):
            out.append(f"{where}: attribute {k} has an e-mail address")
        elif CARD.search(text):
            out.append(f"{where}: attribute {k} has a card-like number")
        elif len(text) > 200 and " " in text:
            out.append(f"{where}: attribute {k} has {len(text)} characters of text")
    return out


def check_folder(folder: Path) -> tuple[list[str], dict]:
    folder = Path(folder)
    problems, counted = [], {"spans": 0, "logs": 0, "metrics": 0}
    for req in lines(folder / "traces.jsonl"):
        for rs in req.get("resourceSpans", []):
            for ss in rs.get("scopeSpans", []):
                for s in ss.get("spans", []):
                    counted["spans"] += 1
                    problems += problems_in(f"span {s['name']}", attributes(s.get("attributes")))
                    for e in s.get("events", []):
                        problems += problems_in(f"span event {e.get('name')}", attributes(e.get("attributes")))
    for req in lines(folder / "logs.jsonl"):
        for rl in req.get("resourceLogs", []):
            for sl in rl.get("scopeLogs", []):
                for r in sl.get("logRecords", []):
                    counted["logs"] += 1
                    problems += problems_in(f"event {r.get('eventName', '')}", attributes(r.get("attributes")))
                    body = r.get("body", {}).get("stringValue", "")
                    if EMAIL.search(body) or CARD.search(body):
                        problems.append(f"event {r.get('eventName', '')}: the body has an e-mail address or a card number")
    for _ in lines(folder / "metrics.jsonl"):
        counted["metrics"] += 1
    return problems, counted
