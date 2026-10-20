"""Larkfield's policy documents and a simple keyword search over their sections."""

import math
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from . import config


@dataclass(frozen=True)
class Section:
    doc_id: str
    version: int
    title: str
    heading: str
    text: str
    language: str
    effective_from: str
    effective_to: str

    @property
    def key(self) -> str:
        return f"{self.doc_id}@{self.version}#{slug(self.heading)}"

    @property
    def link(self) -> str:
        return f"/policies/{self.doc_id}/v{self.version}#{slug(self.heading)}"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", fold(text)).strip("-")


def fold(text: str) -> str:
    """Lower case without accents: 'Électrique' -> 'electrique'."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


STOP = set(
    "a an and are as at be by can do does for from has have how i if in is it its my me of on or our so that the "
    "their them then there this to was we what when where which who will with you your am get got want would could "
    "should please hi hello thanks thank much many any some just about after before into than also not no yes "
    "le la les un une des de du et est je mon ma mes vous votre vos pour que qui quoi quel quelle quand comment "
    "combien dans sur avec pas ne a au aux ce cet cette ces il elle on nous ai suis bonjour merci".split()
)

# A few words that customers use for what the policies call something else (also in French).
SYNONYMS = {
    "money": "refund", "back": "return", "send": "return", "rembourser": "refund", "remboursement": "refund",
    "retour": "return", "retourner": "return", "renvoyer": "return", "livraison": "delivery", "livrer": "delivery",
    "garantie": "warranty", "guarantee": "warranty", "annuler": "cancel", "annulation": "cancel",
    "cancellation": "cancel", "late": "late", "retard": "late", "delay": "late", "delayed": "late",
    "jours": "days", "colis": "parcel", "commande": "order", "points": "points", "carte": "card",
    "cadeau": "gift", "mot": "password", "passe": "password", "broken": "damaged", "endommage": "damaged",
    "casse": "damaged", "plante": "plants", "plant": "plants", "bbq": "bbq", "barbecue": "bbq", "grill": "bbq",
    "kettle": "kettle", "bouilloire": "kettle", "returns": "return", "returned": "return", "refunds": "refund",
    "refunded": "refund", "orders": "order", "days": "days", "shipping": "delivery", "ship": "delivery",
}


def terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", fold(text))
    out = []
    for w in words:
        if w in STOP or len(w) < 2:
            continue
        w = SYNONYMS.get(w, w)
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def _front_matter(raw: str) -> tuple[dict, str]:
    meta, body = {}, raw
    if raw.startswith("---"):
        _, head, body = raw.split("---", 2)
        for line in head.strip().splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return meta, body


@lru_cache(maxsize=1)
def sections() -> tuple[Section, ...]:
    out = []
    for path in sorted(config.POLICIES.glob("*.md")):
        meta, body = _front_matter(path.read_text(encoding="utf-8"))
        parts = re.split(r"^## +(.+)$", body, flags=re.M)
        for heading, text in zip(parts[1::2], parts[2::2]):
            out.append(Section(
                doc_id=meta["doc_id"], version=int(meta["version"]), title=meta["title"], heading=heading.strip(),
                text=text.strip(), language=meta.get("language", "en"),
                effective_from=meta.get("effective_from", ""), effective_to=meta.get("effective_to", ""),
            ))
    return tuple(out)


@lru_cache(maxsize=1)
def _index():
    docs = [terms(f"{s.title} {s.heading} {s.heading} {s.text}") for s in sections()]
    df: dict[str, int] = {}
    for d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    return docs, df


def idf() -> dict[str, float]:
    """How rare each word is in the policies: rare words count more."""
    docs, df = _index()
    return {t: math.log(1 + len(docs) / n) for t, n in df.items()}


def in_force(s: Section, today: str) -> bool:
    """Is this policy version in force on the app's date?"""
    return s.effective_from <= today


def search(query: str, k: int | None = None, today: str | None = None) -> list[tuple[Section, float]]:
    """The k best sections for the query, best first, with their scores."""
    k = k or config.RETRIEVAL_K
    today = today or config.TODAY
    docs, df = _index()
    n = len(docs)
    q = terms(query)
    scored = []
    for s, d in zip(sections(), docs):
        if not in_force(s, today):
            continue
        score = 0.0
        for t in set(q):
            tf = d.count(t)
            if tf:
                score += (1 + math.log(tf)) * math.log(1 + n / df[t])
        if score > 0:
            scored.append((s, round(score / math.sqrt(len(d) + 10) * 4, 3)))
    scored.sort(key=lambda x: (-x[1], x[0].doc_id, -x[0].version))
    return scored[:k]


def find(doc_id: str, version: int | None = None) -> list[Section]:
    return [s for s in sections() if s.doc_id == doc_id and (version is None or s.version == version)]
