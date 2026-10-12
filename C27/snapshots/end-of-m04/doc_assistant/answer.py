"""Ask the model for an answer made of claims, each with the IDs of the passages that support it.

The request uses structured output (a strict JSON schema), so the answer can be checked in code
(cite.py). The prompt files are in prompts/. From the RAG course's project (MIT), with the
shop's name in the prompt: one assistant serves several shops.
"""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from .context import Context

PROMPTS = Path(__file__).resolve().parent / "prompts"
MAX_TOKENS = 2000   # reasoning models count their hidden reasoning in this limit too

SCHEMA = {
    "type": "object",
    "properties": {
        "answerable": {"type": "boolean", "description": "false when the passages do not answer the question"},
        "answer": {"type": "string", "description": "the short answer, in the language of the question"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "one statement of fact from the answer"},
                    "chunk_ids": {"type": "array", "items": {"type": "string"},
                                  "description": "IDs of the passages that support the statement"},
                },
                "required": ["text", "chunk_ids"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["answerable", "answer", "claims"],
    "additionalProperties": False,
}


def load_prompt(name: str) -> tuple[str, str]:
    """prompts/NAME.md -> (system message, user message template)."""
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    system, user = text.split("[user]\n", 1)
    return system.replace("[system]\n", "", 1).strip(), user.strip()


def build_request(question: str, as_of: str, context: Context, model: str, shop: str,
                  prompt: str = "answer_v1") -> dict:
    system, user = load_prompt(prompt)
    return {
        "model": model,
        "messages": [{"role": "system", "content": system.format(shop=shop)},
                     {"role": "user", "content": user.format(as_of=as_of, question=question, passages=context.text())}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "cited_answer", "strict": True, "schema": SCHEMA}},
        "max_completion_tokens": MAX_TOKENS,
    }


@dataclass(frozen=True)
class Claim:
    text: str
    chunk_ids: tuple


@dataclass(frozen=True)
class Answer:
    answerable: bool
    answer: str
    claims: tuple

    def text(self) -> str:
        return " ".join([self.answer, *(c.text for c in self.claims)])

    def cited(self) -> list[str]:
        return list(dict.fromkeys(i for c in self.claims for i in c.chunk_ids))


class ClaimModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    chunk_ids: list[str]


class AnswerModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answerable: bool
    answer: str
    claims: list[ClaimModel]


class AnswerProblem(Exception):
    """The model's output is not a usable answer (cut, refused, not JSON, not the schema)."""


def parse_answer(completion) -> Answer:
    if completion.refusal:
        raise AnswerProblem(f"refused: {completion.refusal}")
    if completion.finish_reason == "length":
        raise AnswerProblem("cut: the answer reached the token limit")
    try:
        data = AnswerModel.model_validate_json(completion.text or "")
    except ValidationError as e:
        raise AnswerProblem(f"not a valid answer: {e.errors()[0]['msg']}") from e
    return Answer(data.answerable, data.answer, tuple(Claim(c.text, tuple(c.chunk_ids)) for c in data.claims))
