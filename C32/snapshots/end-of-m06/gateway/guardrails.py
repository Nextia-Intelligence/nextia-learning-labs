"""Guardrails at the gateway: simple rules on the text of every request, with no knowledge of the task.

Two rules (config/gateway.yaml), and a third kind for your own rules (kind: pattern, a regular expression):
- card-number: 13 to 19 digits (spaces or hyphens allowed between them) that pass the Luhn check, the
  checksum of payment card numbers. Action redact: the number is replaced before the request leaves; or block.
- secret: an API key, a private key or a password written in the text. Action block.

The gateway sees only text: it cannot know whether an answer is right for the task, whether a refund is
allowed, or whether a customer may see an order. Those checks stay in the app (see the lesson).
"""

import re

CARD = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?![\d-])")
NAIVE_CARD = re.compile(r"\b\d{13,19}\b")        # the rule without the checksum, for comparison (measure/)
SECRETS = [
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("practice_key", re.compile(r"\bsim-[a-z]{2}-[A-Za-z0-9-]{6,}")),
    ("estate_secret", re.compile(r"\best-[A-Za-z0-9_-]{20,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("password", re.compile(r"(?i)\bpassword\s*[:=]\s*\S{4,}")),
]
REDACTED = "[card number removed]"


def luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = ord(ch) - 48
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def card_numbers(text: str) -> list[str]:
    out = []
    for m in CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn(digits):
            out.append(m.group(0))
    return out


def secrets_in(text: str) -> list[str]:
    return [name for name, rx in SECRETS if rx.search(text)]


def texts(body: dict) -> list[str]:
    """Every piece of text in a chat or embeddings request that a person or a tool wrote."""
    out = []
    for m in body.get("messages") or []:
        c = m.get("content")
        if isinstance(c, str):
            out.append(c)
        elif isinstance(c, list):
            out += [p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text"]
        for call in m.get("tool_calls") or []:
            out.append(str((call.get("function") or {}).get("arguments", "")))
    inp = body.get("input")
    if isinstance(inp, str):
        out.append(inp)
    elif isinstance(inp, list):
        out += [x for x in inp if isinstance(x, str)]
    return out


def _redact_text(text: str) -> tuple[str, int]:
    n = 0

    def sub(m):
        nonlocal n
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn(digits):
            n += 1
            return REDACTED
        return m.group(0)

    return CARD.sub(sub, text), n


def apply(body: dict, rules: list[dict]) -> tuple[str, dict, list[str]]:
    """Run the rules. Returns (decision, body, notes): decision "pass", "redacted" or "block"."""
    notes = []
    all_text = "\n".join(texts(body))
    for rule in rules:
        if rule["kind"] == "pattern":           # a regular expression from the configuration
            if re.search(rule["pattern"], all_text):
                if rule["action"] == "block":
                    return "block", body, [f"{rule['id']}: the pattern {rule['pattern']} matched"]
                notes.append(f"{rule['id']}: the pattern matched (logged)")
            continue
        if rule["kind"] == "secret":
            found = secrets_in(all_text)
            if found and rule["action"] == "block":
                return "block", body, [f"{rule['id']}: {', '.join(found)}"]
        if rule["kind"] == "card_number":
            found = card_numbers(all_text)
            if not found:
                continue
            if rule["action"] == "block":
                return "block", body, [f"{rule['id']}: {len(found)} card number(s)"]
            body = redact_body(body)
            notes.append(f"{rule['id']}: {len(found)} card number(s) redacted")
    return ("redacted" if notes else "pass"), body, notes


def redact_body(body: dict) -> dict:
    out = dict(body)
    msgs = []
    for m in body.get("messages") or []:
        m = dict(m)
        if isinstance(m.get("content"), str):
            m["content"], _ = _redact_text(m["content"])
        msgs.append(m)
    if "messages" in body:
        out["messages"] = msgs
    if isinstance(body.get("input"), str):
        out["input"], _ = _redact_text(body["input"])
    return out
