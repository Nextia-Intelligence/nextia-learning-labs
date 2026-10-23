"""The recorded answers: request key -> the answers that real models gave to exactly that request.

The key is a SHA-256 of the request body, without the fields that do not change what the request asks
(reasoning_effort, stream, user, metadata, store). Every other field counts, byte for byte: change one
character of a prompt, the schema, the token limit or the deployment name, and the key changes. Then the
simulator has no recording, and it says so. It never invents an answer.

reasoning_effort is checked apart (provsim/features.py): some deployments refuse some values, as the real
ones did, and the answer's headers say which setting the recording was made with.
"""

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

RECORDINGS = Path(__file__).resolve().parent / "recordings" / "answers.jsonl.gz"
IGNORED = ("reasoning_effort", "stream", "stream_options", "user", "metadata", "store")


def request_key(body: dict) -> str:
    content = {k: v for k, v in body.items() if k not in IGNORED}
    text = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class Answer:
    key: str
    deployment: str
    provider: str
    course: str
    file: str
    label: dict
    latency_s: float
    at: str
    reasoning_effort: str | None
    response: dict | None
    error: dict | None

    @property
    def repeat(self) -> int:
        return int(self.label.get("repeat", 1) or 1)

    @property
    def constructed(self) -> bool:
        return self.course == "constructed"


class Store:
    def __init__(self, path: Path = RECORDINGS):
        self.by_key: dict[str, list[Answer]] = {}
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                a = Answer(r["key"], r["deployment"], r["provider"], r["course"], r["file"], r["label"],
                           float(r.get("latency_s") or 0.0), str(r.get("at") or ""), r.get("reasoning_effort"),
                           r.get("response"), r.get("error"))
                self.by_key.setdefault(a.key, []).append(a)
        self._next: dict[str, int] = {}

    def __len__(self) -> int:
        return sum(len(v) for v in self.by_key.values())

    def answers(self, body: dict) -> list[Answer]:
        return self.by_key.get(request_key(body), [])

    def pick(self, body: dict, repeat: int | None = None) -> Answer | None:
        """One recorded answer. With `repeat`, the answer of that recorded repeat (if it exists); otherwise the
        answers of a request with several recordings are given in turn (first, second, ..., then again)."""
        found = self.answers(body)
        if not found:
            return None
        if repeat is not None:
            for a in found:
                if a.repeat == repeat:
                    return a
        key = found[0].key
        i = self._next.get(key, 0)
        self._next[key] = i + 1
        return found[i % len(found)]

    def deployments(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for answers in self.by_key.values():
            for a in answers:
                out[a.deployment] = out.get(a.deployment, 0) + 1
        return out
