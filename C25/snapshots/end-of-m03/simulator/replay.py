"""Replay mode: real recorded answers of the help desk's assistant (the MLOps course).

The evaluation course sent the assistant's triage requests to a real model (chat-small, model
version gpt-6-luna-2026-09-22) for 271 made-up tickets, with prompt v2 and prompt v3, and kept
every answer: 679 calls per prompt (all 271 tickets once, and the 102 development tickets four
more times). recorded_assistant.jsonl.gz keeps, for each call, the request's key, the answer
text, the finish reason, the tokens and the time it took.

When a triage request is one of the recorded requests (the same key: the same model, messages,
schema and token limit, byte for byte), the simulator answers with one of its recorded answers,
after the recorded time. That answer is REPLAYED: a real model wrote it. Any other request gets a
SIMULATED answer (see model.triage_answer): times, tokens and how often the answer is cut off come
from the same recordings, but the text is a template.
"""

import gzip
import hashlib
import json
import random
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).resolve().parent / "recorded_assistant.jsonl.gz"
KEY_FIELDS = ("model", "messages", "response_format", "tools", "max_completion_tokens", "stream")


def request_key(body: dict) -> str:
    """The evaluation course's request key: the same fields in, the same key out."""
    fields = {name: body.get(name) for name in KEY_FIELDS}
    text = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@lru_cache
def recordings() -> dict[str, list[dict]]:
    by_key: dict[str, list[dict]] = {}
    for line in gzip.decompress(FILE.read_bytes()).decode("utf-8").splitlines():
        row = json.loads(line)
        by_key.setdefault(row["key"], []).append(row)
    return by_key


def find(body: dict, rng: random.Random) -> dict | None:
    """One recorded answer to this request (chosen at random among its repeats), or None."""
    rows = recordings().get(request_key(body))
    if not rows:
        return None
    return rows[rng.randrange(len(rows))]
