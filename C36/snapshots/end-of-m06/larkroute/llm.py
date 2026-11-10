"""An LLM as a classifier: the prompt, the answer schema, and a client that replays recorded answers.

By default nothing leaves your computer: `ReplayClient` reads the answers that the course recorded once from a
hosted model (data/recordings/), with their tokens, cost and time. `LiveClient` sends the same prompt to a model
of your own (optional; it needs the `openai` package and your own key, and sends the message text to that
provider: use it only with synthetic data such as this course's).
"""

import json
import os

import pandas as pd

from larkroute.data import ROUTES, data_dir

ROUTE_DESCRIPTIONS = {
    "orders": "changes to an order before it ships: change or cancel an order, a missing order confirmation",
    "delivery": ("where a parcel is, late or missed deliveries, a new delivery day, a parcel marked delivered but "
                 "not received"),
    "returns_refunds": "returns, exchanges, items that arrived damaged or wrong, the status of a refund after a return",
    "billing": "charges and payments: a double or wrong charge, a failed payment, invoices, promotion codes",
    "product": "questions about products: size, materials, stock, assembly, care and warranty, before or after buying",
    "account": ("the customer's Larkfield account: login, personal details, deleting the account, and someone else "
                "using the account"),
    "needs_person": ("a person must read it first: a safety problem, a legal or press threat, or a complaint that asks "
                     "for a manager"),
}
SCHEMA = {"type": "object", "properties": {
    "route": {"type": "string", "enum": ROUTES},
    "confidence": {"type": "number"},
    "reason": {"type": "string"}},
    "required": ["route", "confidence", "reason"], "additionalProperties": False}


def system_prompt(mode: str) -> str:
    """mode: "zero-shot" (the route names only) or "few-shot" (descriptions and similar labelled examples)."""
    if mode == "zero-shot":
        routes = ", ".join(ROUTES)
        return ("You route customer messages for Larkfield, an online shop for home and garden products. "
                f"Choose exactly one route for the message: {routes}. Messages can be in English or French. "
                "Answer in JSON with the route, your confidence from 0 to 1, and a reason of at most 12 words.")
    lines = "\n".join(f"- {r}: {d}" for r, d in ROUTE_DESCRIPTIONS.items())
    return ("You route customer messages for Larkfield, an online shop for home and garden products. Messages can be "
            "in English or French. Choose exactly one route. If a message asks for two things, choose the route of "
            f"the main request (usually the first one).\nRoutes:\n{lines}\n"
            "You also get labelled examples of similar messages. Answer in JSON with the route, your confidence from "
            "0 to 1, and a reason of at most 12 words.")


def user_prompt(text: str, examples: list[tuple[str, str]] | None = None) -> str:
    if not examples:
        return f"Message:\n{text}"
    shown = "\n".join(f"- {t!r} -> {r}" for t, r in examples)
    return f"Labelled examples:\n{shown}\n\nMessage:\n{text}"


class ExamplePicker:
    """Few-shot examples chosen by similarity: the k training messages with the closest TF-IDF vectors."""

    def __init__(self, train: pd.DataFrame, k: int = 8):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.train = train.reset_index(drop=True)
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)
        self.x = self.vec.fit_transform(self.train["text"])
        self.k = k

    def pick(self, text: str) -> list[tuple[str, str]]:
        sims = (self.x @ self.vec.transform([text]).T).toarray().ravel()
        idx = sims.argsort()[::-1][: self.k]
        return [(self.train.at[i, "text"], self.train.at[i, "route"]) for i in sorted(idx)]


class ReplayClient:
    """The recorded answers of one mode ("zero-shot", "few-shot", or "reasoning" for the hard messages)."""

    def __init__(self, mode: str):
        path = data_dir() / "recordings" / f"llm-{mode}.jsonl"
        if not path.exists():
            raise SystemExit(f"No recordings for {mode}: {path}. Run: python get_data.py")
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        self.answers = {r["message_id"]: r for r in rows}
        self.mode = mode

    def classify(self, message_id: str) -> dict:
        if message_id not in self.answers:
            raise KeyError(f"{message_id} has no recorded {self.mode} answer")
        return {**self.answers[message_id], "replayed": True}


class LiveClient:
    """Optional: your own model. Set OPENAI_API_KEY (and LARKROUTE_LLM_BASE_URL, LARKROUTE_LLM_MODEL if needed)."""

    def __init__(self, mode: str, train: pd.DataFrame | None = None):
        from openai import OpenAI  # not in requirements.txt: pip install openai
        self.client = OpenAI(base_url=os.environ.get("LARKROUTE_LLM_BASE_URL"))
        self.model = os.environ.get("LARKROUTE_LLM_MODEL", "gpt-4.1-mini")
        self.mode = mode
        self.picker = ExamplePicker(train) if mode == "few-shot" and train is not None else None

    def classify(self, message_id: str, text: str) -> dict:
        examples = self.picker.pick(text) if self.picker else None
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt(self.mode)},
                      {"role": "user", "content": user_prompt(text, examples)}],
            response_format={"type": "json_schema", "json_schema": {"name": "route", "strict": True, "schema": SCHEMA}})
        return {"message_id": message_id, **parse(r.choices[0].message.content), "model": r.model, "replayed": False}


def parse(answer: str) -> dict:
    """Check an answer: valid JSON, a known route, a confidence from 0 to 1. A bad answer goes to review."""
    try:
        a = json.loads(answer)
        route, conf = a["route"], float(a["confidence"])
    except (ValueError, KeyError, TypeError):
        return {"route": "review", "confidence": 0.0, "reason": "not valid JSON", "valid": False}
    if route not in ROUTES or not 0 <= conf <= 1:
        return {"route": "review", "confidence": 0.0, "reason": f"bad answer: {route!r}, {conf}", "valid": False}
    return {"route": route, "confidence": conf, "reason": str(a.get("reason", "")), "valid": True}
