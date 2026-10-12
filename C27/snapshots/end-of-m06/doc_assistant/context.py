"""The passages that go into the prompt (the RAG course's context assembly, MIT).

1. Keep the search order (the best passage first).
2. Remove near-duplicates: two passages of two different documents whose words are almost the
   same (Jaccard similarity of their word sets >= 0.9). Two versions of the same document are
   NOT merged: their differences are the point, and the dates decide between them.
3. Stop before the budget is used up (tokens estimated as characters / 4).
"""

import math
import re
from dataclasses import dataclass, field

BUDGET = 1500
SIMILAR = 0.9


@dataclass(frozen=True)
class Passage:
    chunk_id: str
    document_id: str
    doc_key: str
    version: str
    title: str
    doc_type: str
    access: str
    effective_from: str
    effective_to: str      # "" when the document has no end date
    section: str
    text: str
    pages: tuple = ()
    score: float = 0.0

    def header(self) -> str:
        dates = f"in force from {self.effective_from}" + (
            f" to {self.effective_to}" if self.effective_to else ", no end date")
        return (f"[{self.chunk_id}] {self.title} | {self.doc_type}, version {self.version}, {dates} | "
                f"section: {self.section or '-'}")

    def formatted(self) -> str:
        return f"{self.header()}\n{self.text}"


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def word_set(text: str) -> set[str]:
    body = text.split("\n", 1)[1] if "\n" in text else text
    return set(re.findall(r"\w+", body.lower()))


def jaccard(a: str, b: str) -> float:
    wa, wb = word_set(a), word_set(b)
    return len(wa & wb) / len(wa | wb) if wa | wb else 1.0


@dataclass
class Context:
    passages: list = field(default_factory=list)
    dropped: list = field(default_factory=list)     # (chunk_id, reason)
    tokens: int = 0

    @property
    def ids(self) -> list[str]:
        return [p.chunk_id for p in self.passages]

    def text(self) -> str:
        return "\n\n".join(p.formatted() for p in self.passages)


def assemble(passages: list[Passage], budget: int = BUDGET) -> Context:
    ctx = Context()
    for p in passages:
        twin = next((c for c in ctx.passages if c.document_id != p.document_id and c.doc_key != p.doc_key
                     and jaccard(c.text, p.text) >= SIMILAR), None)
        if twin is not None:
            ctx.dropped.append((p.chunk_id, f"near-duplicate of {twin.chunk_id}"))
            continue
        cost = estimate_tokens(p.formatted())
        if ctx.tokens + cost > budget:
            ctx.dropped.append((p.chunk_id, "over budget"))
            continue
        ctx.passages.append(p)
        ctx.tokens += cost
    return ctx
