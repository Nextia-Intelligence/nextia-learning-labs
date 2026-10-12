"""The AI work for one ticket: what the API asks the AI provider, and how it reads the answers.

Two tasks for every new ticket (the MLOps course, Module 1):
- triage: the help desk's assistant (assistant.py): the team, whether a person must handle
          the ticket, and a first reply that a person checks before it is sent (a chat model,
          JSON answer). It replaced the scaling course's classify and draft_reply.
- embed:  a vector of the ticket's text, for finding similar tickets (an embedding model)
And one for questions (the scaling course, Module 3): answer, from the shop's documents.

The requests use the OpenAI-compatible API, so the same code talks to the simulated
provider on your computer and to a real provider.
"""

CHAT_MODEL = "chat-small"
EMBED_MODEL = "embed-small"
EMBED_DIMENSIONS = 384
ANSWER_PROMPT = "answer-v1"
EMBEDDING_VERSION = "embed-small-384-v1"

ANSWER_SYSTEM = (
    "You answer questions about Larkfield, an online shop for garden and home products. Use "
    "only the documents and the tickets below the question. If they do not answer it, say that "
    "a person on the help desk will help. Write 1 to 3 short sentences in plain English."
)


def ticket_text(subject: str, body: str) -> str:
    return f"Subject: {subject}\n\n{body}".strip()


def answer_request(question: str, documents: list[dict], tickets: list[dict]) -> dict:
    """A question with its context: the documents the caller may read, and (for a customer)
    their own latest tickets. The answer depends on all of it."""
    parts = [f"Question: {question}", "", "Documents:"]
    parts += [f"- [{d['title']}] {d['body'][:600]}" for d in documents] or ["- (none found)"]
    if tickets:
        parts += ["", "The customer's latest tickets:"]
        parts += [f"- {t['ticket_id']} ({t['status']}): {t['subject']}" for t in tickets]
    return {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": ANSWER_SYSTEM},
            {"role": "user", "content": "\n".join(parts)},
        ],
        "max_completion_tokens": 200,
        "reasoning_effort": "none",
    }


def embed_request(subject: str, body: str) -> dict:
    return {
        "model": EMBED_MODEL,
        "input": ticket_text(subject, body),
        "dimensions": EMBED_DIMENSIONS,
    }


class BadAnswer(ValueError):
    """The provider answered, but not in the agreed shape. Retrying the same request will
    most likely give the same answer, so this is not a reason to retry."""


def parse_draft(answer: dict) -> str:
    """A text answer (an answer to a question)."""
    try:
        text = answer["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise BadAnswer(f"not a reply: {error}") from None
    if not text:
        raise BadAnswer("an empty reply")
    return text


def parse_embedding(answer: dict) -> list[float]:
    try:
        vector = [float(x) for x in answer["data"][0]["embedding"]]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise BadAnswer(f"not an embedding: {error}") from None
    if len(vector) != EMBED_DIMENSIONS:
        raise BadAnswer(f"an embedding with {len(vector)} numbers, not {EMBED_DIMENSIONS}")
    return vector


def usage(answer: dict) -> tuple[int, int]:
    """Tokens in and out, as the provider counted them."""
    u = answer.get("usage") or {}
    return int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))
