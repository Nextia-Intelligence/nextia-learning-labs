"""The help desk's assistant: the triage step of every new ticket (the MLOps course, Module 1).

One request per ticket does what classify and draft_reply did before: it chooses the team,
decides if a person must handle the ticket (Grace's rules H1 to H5), and drafts the reply that
an agent checks. It is the assistant that the evaluation course tested: the same prompt files,
the same policy, the same output schema and the same token limit, so the requests are the
same, byte for byte.

    assistant-v2   the live prompt (the evaluation course's baseline)
    assistant-v3   the candidate that Omar's team wrote (warmer, shorter prompt)

The prompt files are in ticket_api/prompts/. A prompt version is a file name: to change the
prompt, add a new file; never edit a file that a release used.
"""

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ticket_api.ai import BadAnswer

PROMPTS = Path(__file__).resolve().parent / "prompts"
CHAT_MODEL = "chat-small"
MAX_TOKENS = 1000  # room for the reasoning and the JSON answer
DEFAULT_PROMPT = "assistant-v2"
TEAMS = ("delivery", "returns", "payment", "warranty", "account")
SCHEMA_FILE = "ticket_analysis.json"


class NoAnswer(BadAnswer):
    """The model used all its tokens and returned no text: no team, no needs_human, no reply."""


@dataclass(frozen=True)
class Triage:
    team: str
    needs_human: bool
    language: str
    confidence: str
    reason: str
    reply: str


@lru_cache
def load_prompt(version: str) -> tuple[str, str]:
    """The (system, user) templates of prompts/<version>.md, with the policy in the system text.
    The notes above [system] are for people; they are not sent."""
    path = PROMPTS / f"{version}.md"
    if not path.exists():
        raise ValueError(f"no prompt file {path.name}")
    text = path.read_text(encoding="utf-8")
    system, user = text.split("[system]\n", 1)[1].split("[user]\n", 1)
    policy = (PROMPTS / "policy.md").read_text(encoding="utf-8").strip()
    return system.strip().replace("{policy}", policy), user.strip()


@lru_cache
def response_format() -> dict:
    return json.loads((PROMPTS / SCHEMA_FILE).read_text(encoding="utf-8"))


def prompt_versions() -> list[str]:
    return sorted(p.stem for p in PROMPTS.glob("assistant-v*.md"))


def fingerprint(version: str) -> str:
    """A short hash of everything the prompt version sends besides the ticket: the
    instructions, the policy and the output schema. The same fingerprint = the same prompt."""
    system, user = load_prompt(version)
    blob = json.dumps([system, user, response_format(), MAX_TOKENS], ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def ticket_block(message: str) -> str:
    """The customer's message, with the tags that mark it made harmless."""
    text = message.replace("<ticket>", "(ticket)").replace("</ticket>", "(/ticket)")
    return text if text.strip() else "(no text)"


def triage_request(message: str, version: str = DEFAULT_PROMPT) -> dict:
    system, user = load_prompt(version)
    return {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user.replace("{ticket}", ticket_block(message))},
        ],
        "max_completion_tokens": MAX_TOKENS,
        "response_format": response_format(),
    }


def finish_reason(answer: dict) -> str:
    try:
        return str(answer["choices"][0].get("finish_reason") or "unknown")
    except (KeyError, IndexError, TypeError, AttributeError):
        return "unknown"


def parse_triage(answer: dict) -> Triage:
    try:
        content = answer["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as error:
        raise BadAnswer(f"not a triage answer: {error}") from None
    if not content.strip():
        reason = finish_reason(answer)
        raise NoAnswer(f"no answer (finish_reason {reason})")
    try:
        data = json.loads(content)
        triage = Triage(
            team=data["team"],
            needs_human=data["needs_human"],
            language=data.get("language", "en"),
            confidence=data.get("confidence", ""),
            reason=data.get("reason", ""),
            reply=data["reply"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise BadAnswer(f"not a triage answer: {error}") from None
    if (
        triage.team not in TEAMS
        or not isinstance(triage.needs_human, bool)
        or not triage.reply.strip()
    ):
        raise BadAnswer(f"not a triage answer: {triage.team!r}, {triage.needs_human!r}")
    return triage
