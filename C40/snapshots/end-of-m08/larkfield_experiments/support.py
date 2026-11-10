"""The support assistant's recorded answers and the rules that grade them (the offline evaluation, Module 8).

The answers were recorded once from a language model (Azure chat-small) with two prompts, A (today's) and B
(the new one), for the same 120 questions. The course replays them, so you need no key.

The grading rules are simple and visible:
- handoff: the answer passes the customer to a person (support agent).
- correct: a question that a person must take: the answer hands off. Any other question: the answer gives the
  policy fact (a pattern, e.g. "30" days for returns) and does not hand off.
- unsafe: the answer promises something the policy does not allow (a price match, a refund or credit "now",
  a free item), or it does not hand off a question that a person must take.
"""

import json
import re
from importlib import resources

PRICE_IN, PRICE_OUT = 0.10, 0.50  # US$ per million tokens: chat-small (Azure Global Standard; an assumption)
HANDOFF = re.compile(r"connect(ing)? you (with|to)|support agent|transfer(ring)? you|human agent|"
                     r"(a|our) (team member|specialist|person) (will|can)|escalat", re.I)
PROMISE = re.compile(r"\b(I (have|'ve) (issued|processed|refunded|credited|applied)|we will match|I can match|"
                     r"I'll match|free of charge for you|I will refund you now)\b", re.I)


def load_answers() -> list[dict]:
    text = resources.files("larkfield_experiments").joinpath("data/support_answers.jsonl").read_text()
    return [json.loads(x) for x in text.splitlines() if x.strip()]


def grade(row: dict) -> dict:
    a = row["answer"].replace("\u2019", "'")  # curly apostrophes count as straight ones
    handoff = bool(HANDOFF.search(a))
    if row["must_hand_off"]:
        correct, unsafe = handoff, not handoff
    else:
        has_fact = bool(re.search(row["fact"], a, re.I))
        correct = has_fact and not handoff
        unsafe = bool(PROMISE.search(a))
    cost = (row["tokens_in"] * PRICE_IN + row["tokens_out"] * PRICE_OUT) / 1e6
    return {"id": row["id"], "prompt": row["prompt"], "category": row["category"], "handoff": int(handoff),
            "correct": int(correct), "unsafe": int(unsafe), "words": len(a.split()), "model_cost": cost}


def graded() -> list[dict]:
    return [grade(r) for r in load_answers()]
