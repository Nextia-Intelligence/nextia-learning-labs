"""ops privacy FILE: what a telemetry file would show a reader that should not see customers'
words: text attributes, e-mail addresses and card numbers, and the size of the telemetry.

    python -m ops privacy telemetry/ticket-worker.jsonl

It counts what it finds and never prints the text itself. Use it on the files of the three
settings in Lesson 3: content off (the default), content on without redaction (Tomás's "log
everything, just in case"), and content on with redaction.
"""

import json
import re
from collections import Counter
from pathlib import Path

from ops.telemetry import Telemetry, read_records, table

TEXT_KEYS = (
    "ticket.subject",
    "ticket.body",
    "gen_ai.input.messages",
    "gen_ai.output.messages",
    "gen_ai.system_instructions",
    "question.text",
    "answer.text",
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def register(commands) -> None:
    p = commands.add_parser("privacy", help="text, e-mail addresses and size in telemetry")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.set_defaults(run=run)


def scan(paths) -> dict:
    found: Counter = Counter()
    size: Counter = Counter()
    for path in paths:
        for r in read_records(path):
            line = json.dumps(r, ensure_ascii=False)
            size[r.get("signal", "?")] += len(line.encode("utf-8")) + 1
            attrs = r.get("attributes") or {}
            for key in TEXT_KEYS:
                if key in attrs:
                    found[f"attribute {key}"] += 1
            for value in [*attrs.values(), r.get("body")]:
                if isinstance(value, str):
                    found["e-mail address"] += len(EMAIL.findall(value))
                    found["card number"] += len(CARD.findall(value))
    return {"found": +found, "size": size}


def run(args) -> int:
    result = scan(args.file)
    tickets = len({t for t in Telemetry.load(*args.file).tickets()})
    total = sum(result["size"].values())
    rows = [
        [signal, f"{n / 1024:,.1f}", f"{n / tickets / 1024:,.2f}" if tickets else "-"]
        for signal, n in sorted(result["size"].items())
    ]
    rows.append(
        ["all", f"{total / 1024:,.1f}", f"{total / tickets / 1024:,.2f}" if tickets else "-"]
    )
    print(f"{', '.join(Path(p).name for p in args.file)}: {tickets:,} tickets")
    print(table(rows, ["signal", "KB", "KB per ticket"]))
    if not result["found"]:
        print("No text attribute, no e-mail address, no card number found.")
        return 0
    print("FOUND (counts only; the text is not printed):")
    for what, n in result["found"].most_common():
        print(f"  {what}: {n:,}")
    return 1
