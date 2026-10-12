"""The answer format: one JSON object with exactly two keys, and the strict check of a model's reply.

    {"team": "payment", "needs_human": false}
"""

import json

TEAMS = ("delivery", "returns", "payment", "warranty", "account")

# The short instruction. The adapter is trained with it, and the base model is tested with it.
SYSTEM_PROMPT = (
    "You sort support tickets for Larkfield, a home and garden shop. Reply with JSON only, in this form: "
    '{"team": "delivery" or "returns" or "payment" or "warranty" or "account", "needs_human": true or false}'
)


def format_answer(team: str, needs_human: bool) -> str:
    """The one way to write an answer. Training examples use it, so the model sees one format only."""
    return json.dumps({"team": team, "needs_human": bool(needs_human)})


def parse_answer(raw: str) -> tuple[dict | None, str]:
    """(answer, "") when the reply is exactly one valid answer, else (None, the problem)."""
    text = raw.strip()
    if not text:
        return None, "empty reply"
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        try:
            value, end = json.JSONDecoder().raw_decode(text)
        except json.JSONDecodeError:
            return None, "not JSON"
        if text[end:].strip():
            return None, "JSON with extra text"
    if not isinstance(value, dict):
        return None, "not a JSON object"
    if set(value) != {"team", "needs_human"}:
        return None, "wrong keys"
    if value["team"] not in TEAMS:
        return None, "unknown team"
    if not isinstance(value["needs_human"], bool):
        return None, "needs_human is not true or false"
    return {"team": value["team"], "needs_human": value["needs_human"]}, ""
