"""The adapter: the only code that talks to a chat model (the LLM applications course's pattern).

The pipeline builds a request (a dict in the Chat Completions format) and gets back a
`Completion`. Three providers, chosen by ANSWER_PROVIDER:

- mock:     no model at all. It copies the first sentence of the best passage and cites it. Fast,
            free and repeatable: for building and testing the rest of the product first.
- recorded: the course team's recorded answers of a real model (chat-small), replayed. A question
            that was not recorded gets the mock's answer, and `note` says so.
- live:     any OpenAI-compatible endpoint (your own key; Azure OpenAI, OpenAI, a local server).
            One call has a timeout, and a timeout, an HTTP 429 or a 5xx is tried again at most
            PROVIDER_RETRIES times, with a growing wait (Module 4). Every other error is not
            tried again: the same request would fail the same way.

How the recorded provider finds a recording (the RAG course's robust replay): by the model, the
prompt (system message and template), the question and its date, NOT the passages. If your
search found other passages than the recorded ones, it still replays the recording and `note`
says "Recorded with passages ...; yours: ...", but only if every passage that the recorded
answer cites is among yours. Otherwise it would show you an answer made from passages you
did not get (for a read-only member: staff-only text), so the mock answers instead, and says why.
"""

import hashlib
import json
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

RECORDINGS = Path(__file__).resolve().parent.parent / "recordings"
PASSAGE_ID = re.compile(r"^\[([0-9a-f]{12})\] ", re.M)
# US dollars per million tokens (input, output), from the provider's price list (Azure, chat-small)
PRICES = {"chat-small": (0.10, 0.50), "chat-strong": (2.00, 10.00)}


class ProviderError(Exception):
    """The provider could not give an answer. `kind`: timeout, rate_limited, unavailable, refused, bad_request."""

    def __init__(self, kind: str, message: str, attempts: int = 1, retry_after: float | None = None):
        super().__init__(message)
        self.kind, self.attempts, self.retry_after = kind, attempts, retry_after


@dataclass
class Completion:
    text: str | None
    finish_reason: str
    refusal: str | None
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    attempts: int = 1
    note: str = ""
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def cost_usd(self) -> float:
        price = PRICES.get(self.model)
        if not price:
            return 0.0
        return (self.input_tokens * price[0] + self.output_tokens * price[1]) / 1_000_000

    @classmethod
    def from_response(cls, data: dict, latency_s: float, provider: str, model: str) -> "Completion":
        choice = data["choices"][0]
        message = choice["message"]
        usage = data.get("usage") or {}
        return cls(text=message.get("content"), finish_reason=choice.get("finish_reason") or "",
                   refusal=message.get("refusal"), model=model, provider=provider,
                   input_tokens=usage.get("prompt_tokens", 0), output_tokens=usage.get("completion_tokens", 0),
                   latency_s=latency_s, raw=data)


def without_passages(request: dict) -> dict:
    messages = [dict(m, content=m["content"].split("\nPassages:\n", 1)[0]) if m.get("role") == "user" else m
                for m in request.get("messages") or []]
    return {**request, "messages": messages}


def replay_key(request: dict) -> str:
    """The model, the messages without the passages, the answer schema and the token limit."""
    r = without_passages(request)
    fields = {k: r.get(k) for k in ("model", "messages", "response_format", "max_completion_tokens")}
    text = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def passage_ids(request: dict) -> list[str]:
    users = [m["content"] for m in request.get("messages") or [] if m.get("role") == "user"]
    return PASSAGE_ID.findall(users[-1]) if users else []


def passages(request: dict) -> list[tuple[str, str]]:
    """(chunk ID, passage text without its header line) for every passage in the request."""
    users = [m["content"] for m in request.get("messages") or [] if m.get("role") == "user"]
    if not users or "\nPassages:\n" not in users[-1]:
        return []
    out = []
    for part in re.split(r"\n\n(?=\[[0-9a-f]{12}\] )", users[-1].split("\nPassages:\n", 1)[1].strip()):
        m = PASSAGE_ID.match(part)
        if m:
            lines = part.split("\n")[1:]
            out.append((m[1], "\n".join(lines)))
    return out


def cited_ids(entry: dict) -> set[str]:
    """The passage IDs that a recorded answer cites."""
    try:
        data = json.loads(entry["response"]["choices"][0]["message"]["content"] or "{}")
        return {i for claim in data.get("claims", []) for i in claim.get("chunk_ids", [])}
    except (ValueError, KeyError, TypeError, AttributeError):
        return set()


class MockProvider:
    """No model: the first sentence of the best passage, cited. Labelled "mock" everywhere."""

    name = "mock"

    def complete(self, request: dict) -> Completion:
        found = passages(request)
        if not found:
            data = {"answerable": False, "answer": "The documents do not say.", "claims": []}
        else:
            cid, text = found[0]
            body = [ln for ln in text.split("\n")[1:] if ln.strip()]   # [0] is the document title
            while len(body) > 1 and not body[0].rstrip().endswith((".", "?", "!", ":")) and len(body[0].split()) <= 8:
                body = body[1:]                                          # a heading line
            sentence = re.split(r"(?<=[.!?])\s", " ".join(body).strip())[0]
            data = {"answerable": True, "answer": sentence, "claims": [{"text": sentence, "chunk_ids": [cid]}]}
        return Completion(json.dumps(data), "stop", None, "mock", "mock")


class RecordedProvider:
    name = "recorded"

    def __init__(self, folder: Path = RECORDINGS):
        self.by_key: dict[str, list[dict]] = {}
        for path in sorted(folder.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                entry = json.loads(line)
                self.by_key.setdefault(replay_key(entry["request"]), []).append(entry)
        self.mock = MockProvider()

    def complete(self, request: dict) -> Completion:
        found = self.by_key.get(replay_key(request))
        if not found:
            c = self.mock.complete(request)
            c.note = "No recording for this question: the mock made this answer from your passages."
            return c
        yours = passage_ids(request)
        usable = [e for e in found if cited_ids(e) <= set(yours)]
        if not usable:
            c = self.mock.complete(request)
            c.note = ("The recorded answer cites passages that your search did not find: the mock made this answer "
                      "from your passages.")
            return c
        entry = max(usable, key=lambda e: len(set(passage_ids(e["request"])) & set(yours)))
        c = Completion.from_response(entry["response"], entry["latency_s"], "recorded", request["model"])
        recorded = passage_ids(entry["request"])
        if recorded != yours:
            c.note = (f"Recorded with passages {', '.join(recorded) or 'none'}; yours: {', '.join(yours) or 'none'}. "
                      "The recorded answer is replayed; its citations are checked against your passages.")
        return c


class LiveProvider:
    """An OpenAI-compatible Chat Completions endpoint, with a timeout and bounded retries."""

    name = "live"

    def __init__(self, base_url: str, api_key: str, timeout_s: float = 20.0, retries: int = 2,
                 sleep=time.sleep):
        from openai import OpenAI

        # Azure reads the key from the api-key header, other providers from Authorization: send both.
        self.client = OpenAI(base_url=base_url, api_key=api_key or "not-needed", timeout=timeout_s,
                             max_retries=0, default_headers={"api-key": api_key} if api_key else None)
        self.retries, self.sleep = retries, sleep

    def _once(self, request: dict) -> dict:
        import openai

        try:
            return self.client.chat.completions.create(**request).model_dump()
        except openai.APITimeoutError:
            raise ProviderError("timeout", "The model did not answer in time.") from None
        except openai.RateLimitError as e:
            after = e.response.headers.get("retry-after") if e.response is not None else None
            raise ProviderError("rate_limited", "The model provider is busy (HTTP 429).",
                                retry_after=float(after) if after and after.isdigit() else None) from None
        except openai.APIStatusError as e:
            if e.status_code >= 500:
                raise ProviderError("unavailable", f"The model provider failed (HTTP {e.status_code}).") from None
            raise ProviderError("bad_request", f"The model provider refused the request (HTTP {e.status_code}).") \
                from None
        except openai.APIConnectionError:
            raise ProviderError("unavailable", "Cannot reach the model provider.") from None

    def complete(self, request: dict) -> Completion:
        start = time.monotonic()
        for attempt in range(1, self.retries + 2):
            try:
                data = self._once(request)
                c = Completion.from_response(data, round(time.monotonic() - start, 3), "live", request["model"])
                c.attempts = attempt
                return c
            except ProviderError as e:
                e.attempts = attempt
                if e.kind not in ("timeout", "rate_limited", "unavailable") or attempt > self.retries:
                    raise
                wait = min(e.retry_after or 2 ** (attempt - 1), 10) * random.uniform(0.8, 1.2)
                self.sleep(wait)
        raise AssertionError("unreachable")


def make_provider(settings) -> MockProvider | RecordedProvider | LiveProvider:
    if settings.answer_provider == "mock":
        return MockProvider()
    if settings.answer_provider == "recorded":
        return RecordedProvider()
    if settings.answer_provider == "live":
        if not settings.llm_base_url:
            raise ValueError("ANSWER_PROVIDER=live needs LLM_BASE_URL (and LLM_API_KEY).")
        return LiveProvider(settings.llm_base_url, settings.llm_api_key, settings.provider_timeout_s,
                            settings.provider_retries)
    raise ValueError(f"Unknown ANSWER_PROVIDER {settings.answer_provider!r}: use mock, recorded or live.")
