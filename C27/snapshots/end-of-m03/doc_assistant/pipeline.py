"""One question, from the caller to a stored answer with its evidence (the vertical slice):

    retrieve -> assemble -> generate -> parse -> check citations -> store

Every step is a span of the question's trace (tracing.py). The shop comes from the caller's
membership, never from the question. If the search finds no passage, the model is not called:
the answer is "the documents do not answer this" (it costs nothing and cannot invent anything).
"""

import time
from dataclasses import dataclass, field

from psycopg.types.json import Jsonb

from . import retrieve
from .access import Principal
from .answer import AnswerProblem, build_request, parse_answer
from .cite import check_answer
from .context import assemble
from .errors import ApiError
from .providers import ProviderError
from .tracing import current_trace_id, tracer

NO_PASSAGES = "The documents do not answer this question."


@dataclass
class Deps:
    db: object
    settings: object
    embedder: object
    provider: object
    reranker: object = None


@dataclass
class Result:
    answer_id: str
    answerable: bool
    answer: str
    claims: list = field(default_factory=list)       # [{text, citations: [...], problems: [...]}]
    passages: list = field(default_factory=list)     # what the model saw
    needs_review: bool = False
    note: str = ""
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    generation_ms: int = 0           # the model call alone (for a recorded answer: its recorded time)
    attempts: int = 0
    trace_id: str = ""


def citation(p) -> dict:
    return {"chunk_id": p.chunk_id, "document_id": p.document_id, "title": p.title, "doc_key": p.doc_key,
            "version": p.version, "section": p.section, "access": p.access}


PROVIDER_ERRORS = {
    "timeout": (504, "provider_timeout", "The model did not answer in time. Your question was not saved; try again."),
    "rate_limited": (503, "provider_busy", "The model provider is busy. Try again in a minute."),
    "unavailable": (503, "provider_unavailable", "The model provider is not available. Try again later."),
    "bad_request": (502, "provider_error", "The model provider refused the request."),
}


def ask(deps: Deps, who: Principal, question: str, as_of: str | None = None) -> Result:
    s = deps.settings
    as_of = as_of or s.today_date()
    start = time.monotonic()
    with tracer().start_as_current_span("ask", attributes={"tenant": who.tenant_id, "question.chars": len(question),
                                                           "prompt": s.prompt_version}) as span:
        with deps.db.tenant(who.tenant_id) as conn:
            with tracer().start_as_current_span("retrieve") as sp:
                found = retrieve.search(conn, question, who.tenant_id, who.access_levels, as_of, deps.embedder, s)
                sp.set_attribute("passages", len(found))
        context = assemble(found)
        result = Result("", False, NO_PASSAGES, passages=[citation(p) | {"score": p.score} for p in context.passages],
                        trace_id=current_trace_id())
        if context.passages:
            request = build_request(question, as_of, context, s.answer_model, who.shop, s.prompt_version)
            with tracer().start_as_current_span("generate") as sp:
                try:
                    completion = deps.provider.complete(request)
                except ProviderError as e:
                    sp.set_attribute("error", e.kind)
                    sp.set_attribute("attempts", e.attempts)
                    status, code, message = PROVIDER_ERRORS[e.kind]
                    raise ApiError(status, code, message,
                                   headers={"Retry-After": "30"} if status == 503 else None) from None
                sp.set_attribute("provider", completion.provider)
                sp.set_attribute("model", completion.model)
                sp.set_attribute("attempts", completion.attempts)
                sp.set_attribute("tokens.input", completion.input_tokens)
                sp.set_attribute("tokens.output", completion.output_tokens)
            try:
                answer = parse_answer(completion)
            except AnswerProblem as e:
                raise ApiError(502, "provider_bad_answer", f"The model's answer could not be used ({e}).") from None
            with tracer().start_as_current_span("check") as sp, deps.db.tenant(who.tenant_id) as conn:
                known = retrieve.lookup(conn, who.tenant_id, who.access_levels, answer.cited())
                checks = check_answer(answer, known, context.ids, f"{question} {as_of}")
                sp.set_attribute("claims", len(checks))
                sp.set_attribute("claims.flagged", sum(not c.ok for c in checks))
            result.answerable, result.answer = answer.answerable, answer.answer
            result.claims = [{"text": c.text, "citations": [citation(known[i]) for i in c.chunk_ids if i in known],
                              "problems": c.problems} for c in checks]
            result.needs_review = answer.answerable and any(
                p.startswith(("missing_id", "not_in_context", "no_citation")) for c in checks for p in c.problems)
            result.note, result.provider, result.model = completion.note, completion.provider, completion.model
            result.input_tokens, result.output_tokens = completion.input_tokens, completion.output_tokens
            result.cost_usd, result.attempts = completion.cost_usd, completion.attempts
            result.generation_ms = round(completion.latency_s * 1000)
        else:
            result.provider, result.model = "none", "none"
        result.latency_ms = round((time.monotonic() - start) * 1000)
        span.set_attribute("answerable", result.answerable)
        with tracer().start_as_current_span("store"), deps.db.tenant(who.tenant_id) as conn:
            cited_docs = sorted({c["document_id"] for claim in result.claims for c in claim["citations"]})
            row = conn.execute(
                "INSERT INTO answers (tenant_id, user_id, question, as_of, answerable, answer, citations, cited_documents,"
                " checks, provider, model, input_tokens, output_tokens, cost_usd, latency_ms, trace_id)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s::uuid[], %s, %s, %s, %s, %s, %s, %s, %s) RETURNING answer_id",
                (who.tenant_id, who.user_id, question, as_of, result.answerable, result.answer,
                 Jsonb(result.claims), cited_docs, Jsonb({"needs_review": result.needs_review, "note": result.note,
                                                          "passages": [p["chunk_id"] for p in result.passages]}),
                 result.provider, result.model, result.input_tokens, result.output_tokens, result.cost_usd,
                 result.latency_ms, result.trace_id)).fetchone()
        result.answer_id = str(row["answer_id"])
        return result
