"""The instrumentation: spans, metrics and audit events for model calls, tool calls, writes and decisions.

The workflow's own files call these functions at the points where something happens (runner.py,
tools.py, execute.py, agent.py, live.py). Each function records:
- a span with the GenAI attribute names (conventions.py) and Larkfield's own (larkfield.*),
- the metrics of that step,
- for decisions, data access and changes: an audit event with the fixed schema (auditstore/schema.py).

What is never recorded: the ticket text, the prompt, the model's answer, the reply, tool results
(only their status and IDs), argument values other than IDs and amounts, names, e-mail addresses.
"""

import contextlib
import contextvars
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from opentelemetry.trace import SpanKind, Status, StatusCode

from . import conventions as c
from . import telemetry

AGENT_ID = "support-workflow"      # the workflow's registration in the agents governance course
AGENT_NAME = "support-resolver"
WORKFLOW = "support-resolution"
PROVIDERS = {"chat-small": "azure.ai.openai", "chat-strong": "azure.ai.openai", "gemma3:4b": "ollama"}
PROMPTS = {"agent": "agent", "agent_structured": "agent_structured", "router": "router", "fixed": "draft",
           "workers_investigator": "investigator", "workers_resolver": "resolver", "draft": "draft"}
READ_KIND = {"get_order": "read", "get_customer_orders": "read", "get_payments": "read", "search_policy": "read"}
CUSTOMER_DATA = ("get_order", "get_customer_orders", "get_payments")


@dataclass
class Run:
    """What every span and audit event of one run needs to know."""
    run_id: str
    ticket_id: str
    customer_id: str
    language: str = ""
    variant: str = ""
    model: str = ""
    release: str = ""
    injection: dict = field(default_factory=dict)   # the practice data's markers (data/injection_markers.json)


_run: contextvars.ContextVar[Run | None] = contextvars.ContextVar("run", default=None)


@contextlib.contextmanager
def run_context(run: Run):
    token = _run.set(run)
    try:
        yield run
    finally:
        _run.reset(token)


def current() -> Run | None:
    return _run.get()


def run_attributes(run: Run) -> dict:
    return {c.RUN_ID: run.run_id, c.TICKET_ID: run.ticket_id, c.CUSTOMER_ID: run.customer_id,
            c.LANGUAGE: run.language, c.VARIANT: run.variant, c.RELEASE: run.release or telemetry.get().release}


def utc(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ the run

_MARKERS = None


def markers() -> dict:
    global _MARKERS
    if _MARKERS is None:
        from .data import DATA
        path = DATA / "injection_markers.json"
        _MARKERS = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return _MARKERS


LANG_WORDS = {"fr": [" le ", " la ", " ma ", " mon ", " est ", " pas ", " vous ", " je ", " bonjour"],
              "de": [" der ", " die ", " das ", " ich ", " ist ", " nicht ", " und ", " meine ", " hallo"]}


def language_of(text: str) -> str:
    """A slice label from the ticket's words: fr, de, or en (the default); the text itself is never recorded."""
    t = f" {text.lower().replace(',', ' ')} "
    scores = {lang: sum(t.count(w) for w in words) for lang, words in LANG_WORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "en"


def new_run(task, state, release: str = "") -> Run:
    return Run(run_id=state.run_id, ticket_id=task.task_id, customer_id=task.customer_id,
               language=language_of(task.text), variant=state.variant, model=state.model, release=release,
               injection=markers())


@contextlib.contextmanager
def run_span(state, task):
    """The root span of a run (trace 1): the agent or the workflow, from the ticket to the proposal."""
    t = telemetry.get()
    run = current()
    if not t.enabled:
        yield None
        return
    agent = state.variant in ("agent", "agent_structured")
    name = f"invoke_agent {AGENT_NAME}" if agent else f"invoke_workflow {WORKFLOW}"
    attrs = {c.OPERATION: c.OP_AGENT if agent else c.OP_WORKFLOW, c.AGENT_NAME: AGENT_NAME if agent else None,
             c.AGENT_ID: AGENT_ID, c.AGENT_VERSION: telemetry.VERSION, c.WORKFLOW_NAME: WORKFLOW,
             c.REQUEST_MODEL: state.model, c.CONVERSATION_ID: state.run_id, **run_attributes(run)}
    ticket_marker = markers().get("tickets", {}).get(task.task_id)
    if ticket_marker:
        attrs[c.INJECTION] = True
        attrs[c.INJECTION_ASK] = ticket_marker
    start = telemetry.clock().now()
    with t.span(name, attrs) as span:
        state.telemetry["root"] = telemetry.span_ref(span)
        yield span
    t.agent_duration.record((telemetry.clock().now() - start) / 1e9,
                            {c.OPERATION: attrs[c.OPERATION], c.REQUEST_MODEL: state.model})
    t.steps.record(state.usage.model_calls, {c.REQUEST_MODEL: state.model, c.VARIANT: state.variant})


def run_finished(span, state) -> None:
    """The proposal (or the stop) on the root span, and the proposal's audit event."""
    if span is None:
        return
    p = state.proposal
    u = state.usage
    span.set_attributes(telemetry.clean({
        c.PROPOSED: p.outcome if p else None, c.RULE: p.rule if p else None, c.ACTIONS: len(p.actions) if p else 0,
        c.STOP_REASON: state.stop_reason or None, c.STEP: state.step, c.INPUT_TOKENS: u.input_tokens,
        c.OUTPUT_TOKENS: u.output_tokens, "larkfield.model_calls": u.model_calls, "larkfield.tool_calls": len(state.evidence),
        "larkfield.status": state.status}))
    if state.stop_reason and state.stop_reason != "finished":
        span.set_attribute(c.ERROR_TYPE, state.stop_reason)
        if state.stop_reason in ("provider_error", "no_recording", "too_many_errors", "max_steps", "repeated_call",
                                 "time", "cost"):
            span.set_status(Status(StatusCode.ERROR, state.stop_reason))


