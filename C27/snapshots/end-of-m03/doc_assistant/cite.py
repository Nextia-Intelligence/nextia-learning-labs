"""Check the citations of an answer in code: what code can check, and what it cannot.
(The RAG course's checks, MIT.) For every claim:

1. exists:      every cited ID is a chunk of THIS shop. (Fails: a made-up ID, or another shop's.)
2. in_context:  every cited ID was in the passages given to the model.
3. cited:       the claim cites at least one passage.
4. numbers:     every number and code in the claim appears in a cited passage (with its header)
                or in the question and its date.
5. words:       at least half of the claim's content words appear in the cited passages.
Checks 4 and 5 are clues, not proof: a claim can share every word with a passage and still say
the opposite. A person decides those.
"""

import re
from dataclasses import dataclass, field

STOP = set("""a an and are as at be by can cannot do does for from has have if in into is it its may must no not of on
or our that the their them then there these they this to under up was we were what when where which who will with
within without you your le la les un une des de du et est en pour pas dans par sur au aux ce qui que se sa son ses
vous votre vos il elle ne ou si plus""".split())
NUMBER = re.compile(r"\b[A-Z]{2,4}(?:-[A-Z0-9]+)+\b|\d+(?:[.,]\d+)?")


def numbers(text: str) -> set[str]:
    text = re.sub(r"(\d),(\d{3})\b", r"\1\2", text)
    found = {n.replace(",", ".") for n in NUMBER.findall(text)}
    return {(n.lstrip("0") or "0") if n.isdigit() else n for n in found}


def content_words(text: str) -> set[str]:
    words = {w for w in re.findall(r"[a-zà-ÿ]+", text.lower()) if w not in STOP and len(w) > 2}
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words}


@dataclass
class ClaimCheck:
    text: str
    chunk_ids: tuple
    problems: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def to_dict(self) -> dict:
        return {"text": self.text, "chunk_ids": list(self.chunk_ids), "problems": self.problems}


def check_claim(claim, known: dict, context_ids: list[str], question: str = "") -> ClaimCheck:
    """known: chunk ID -> Passage, for the cited IDs that exist in this shop."""
    result = ClaimCheck(claim.text, tuple(claim.chunk_ids))
    if not claim.chunk_ids:
        result.problems.append("no_citation")
        return result
    cited = []
    for cid in claim.chunk_ids:
        p = known.get(cid)
        if p is None:
            result.problems.append(f"missing_id:{cid}")
            continue
        if cid not in context_ids:
            result.problems.append(f"not_in_context:{cid}")
        cited.append(p)
    if not cited:
        return result
    source = " ".join(p.formatted() for p in cited)
    missing = sorted(numbers(claim.text) - numbers(source) - numbers(question))
    if missing:
        result.problems.append("number_not_found:" + ",".join(missing))
    words = content_words(claim.text)
    if words:
        share = len(words & content_words(source)) / len(words)
        if share < 0.5:
            result.problems.append(f"unsupported:{share:.2f}")
    return result


def check_answer(answer, known: dict, context_ids: list[str], question: str = "") -> list[ClaimCheck]:
    return [check_claim(c, known, context_ids, question) for c in answer.claims]
