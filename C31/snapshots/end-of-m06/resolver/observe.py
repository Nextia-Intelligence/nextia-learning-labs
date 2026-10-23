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
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from opentelemetry.trace import SpanKind, Status, StatusCode

from . import conventions as c
from . import telemetry
from .usage import PRICES_CHECKED, cost_usd

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


# ------------------------------------------------------------------ audit events

def audit(kind: str, actor: dict, action: dict, *, subject: dict | None = None, authority: dict | None = None,
          evidence: list | None = None, event_id: str | None = None) -> str:
    """Emit one audit event (an OpenTelemetry event named larkfield.audit.<kind>). Returns its event ID."""
    t = telemetry.get()
    run = current()
    from opentelemetry import trace
    ctx = trace.get_current_span().get_span_context()
    event_id = event_id or telemetry.new_id()
    event = {"schema": "larkfield.audit/1", "event_id": event_id, "type": kind,
             "at": utc(telemetry.clock().now()), "actor": actor,
             "run_id": run.run_id if run else "", "ticket_id": run.ticket_id if run else "",
             "trace_id": f"{ctx.trace_id:032x}" if ctx.is_valid else "",
             "span_id": f"{ctx.span_id:016x}" if ctx.is_valid else "",
             "subject": {**({"customer_id": run.customer_id} if run else {}), **(subject or {})},
             "action": action, "authority": authority or {}, "evidence": evidence or []}
    t.event(f"larkfield.audit.{kind}", {"audit.event_id": event_id, "audit.type": kind,
                                        c.RUN_ID: event["run_id"], c.TICKET_ID: event["ticket_id"]}, body=event)
    return event_id


def agent_actor(model: str = "") -> dict:
    run = current()
    return {"kind": "agent", "id": AGENT_ID, "role": run.variant if run else "", "model": model or (run.model if run else "")}


SYSTEM = {"kind": "system", "id": AGENT_ID, "role": "executor"}


# ------------------------------------------------------------------ model calls

def observed(complete):
    """Wrap a provider's complete(request, meta): one `chat` span per call, tokens and cost on it."""
    from .providers import ProviderError

    def call(request: dict, meta: dict | None = None):
        t = telemetry.get()
        if not t.enabled:
            return complete(request, meta)
        meta = meta or {}
        model = request.get("model", "")
        prompt = PROMPTS.get(meta.get("variant") or "", meta.get("variant") or "")
        attrs = {c.OPERATION: c.OP_CHAT, c.PROVIDER: PROVIDERS.get(model, "unknown"), c.REQUEST_MODEL: model,
                 c.REQUEST_MAX_TOKENS: request.get("max_completion_tokens"), c.STEP: meta.get("step"),
                 c.PROMPT_NAME: prompt or None, c.PROMPT_VERSION: telemetry.prompt_version(prompt) if prompt else None,
                 c.OUTPUT_TYPE: "json" if request.get("response_format") else "text",
                 c.CONVERSATION_ID: current().run_id if current() else None}
        if telemetry.CONTENT:   # opt-in only, for the redaction exercise: the Collector must remove it
            attrs["gen_ai.input.messages"] = json.dumps(request.get("messages"), ensure_ascii=False)
        with t.span(f"chat {model}", attrs, kind=SpanKind.CLIENT) as span:
            start = telemetry.clock().now()
            try:
                completion = complete(request, meta)
            except ProviderError as e:
                code = "content_filter" if "content_filter" in str(e) or "content management" in str(e) else (
                    str(e.status) if e.status else type(e).__name__)
                span.set_status(Status(StatusCode.ERROR, code))
                span.set_attribute(c.ERROR_TYPE, code)
                telemetry.clock().advance(0.4)   # a refusal comes back fast; the time is not recorded
                raise
            latency = completion.latency_s or 0.0
            telemetry.clock().advance(latency)
            priced = model
            if cost_usd(model, 1, 1) is None and span.attributes.get(c.GATEWAY_MODEL):
                # a capability name (strong-reasoning) has no price: price the model that answered, as the gateway says
                priced = str(span.attributes[c.GATEWAY_MODEL]).split(" ")[0]
                span.set_attribute("larkfield.priced_as", priced)
            cost = cost_usd(priced, completion.input_tokens, completion.output_tokens)
            span.set_attributes(telemetry.clean({c.COST: round(cost, 8) if cost is not None else None,
                                                 c.PRICE_TABLE: PRICES_CHECKED}))
            span.set_attributes(telemetry.clean({
                c.RESPONSE_MODEL: completion.model or model, c.INPUT_TOKENS: completion.input_tokens,
                c.OUTPUT_TOKENS: completion.output_tokens, c.REASONING_TOKENS: completion.reasoning_tokens or None,
                c.FINISH_REASONS: [completion.finish_reason] if completion.finish_reason else None,
                c.REPLAYED: "inexact" if completion.note else ("exact" if completion.recorded_at else "live"),
                c.RECORDED_LATENCY: latency, "larkfield.model.requested": requested(completion) or None}))
            labels = {c.OPERATION: c.OP_CHAT, c.PROVIDER: PROVIDERS.get(model, "unknown"), c.REQUEST_MODEL: model,
                      c.RESPONSE_MODEL: completion.model or model}
            t.inference_duration.record((telemetry.clock().now() - start) / 1e9, labels)
            if completion.input_tokens:
                t.input_tokens.add(completion.input_tokens, labels)
            if completion.output_tokens:
                t.output_tokens.add(completion.output_tokens, labels)
            return completion

    call.observed = True
    return call


def requested(completion) -> list[str]:
    """The steps the model asked for, as tool(argument names): get_order(order_id). Never the values."""
    out = []
    for call in completion.tool_calls or []:
        try:
            args = json.loads(call.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        out.append(f"{call.name}({args_shape(args) if isinstance(args, dict) else 'raw'})")
    if not out and completion.text and completion.text.lstrip().startswith("{"):
        try:
            step = json.loads(completion.text)
        except json.JSONDecodeError:
            return out
        if isinstance(step, dict) and step.get("tool"):
            names = [k for k in ("order_id", "query") if step.get(k) is not None]
            out.append(f"{step['tool']}({','.join(names) or '-'})")
        elif isinstance(step, dict) and step.get("outcome"):
            out.append("finish(resolution)")
    return out


# ------------------------------------------------------------------ reads

def args_shape(arguments) -> str:
    if isinstance(arguments, dict):
        return ",".join(sorted(arguments)) or "-"
    return "raw"


@contextlib.contextmanager
def tool_span(name: str, arguments, kind: str = "read", extra: dict | None = None):
    t = telemetry.get()
    if not t.enabled:
        yield None
        return
    attrs = {c.OPERATION: c.OP_TOOL, c.TOOL_NAME: name, c.TOOL_TYPE: "function", c.TOOL_KIND: kind,
             c.ARGS_SHAPE: args_shape(arguments), **(extra or {})}
    if isinstance(arguments, dict) and isinstance(arguments.get("order_id"), str):
        attrs[c.ORDER_ID] = arguments["order_id"][:12]
    with t.span(f"execute_tool {name}", attrs) as span:
        started, start_ns = time.perf_counter(), telemetry.clock().now()
        yield span
        telemetry.clock().advance(time.perf_counter() - started)
        t.tool_duration.record((telemetry.clock().now() - start_ns) / 1e9, {c.TOOL_NAME: name, c.TOOL_KIND: kind})


def read_result(span, name: str, arguments, result) -> None:
    """Status, error and injection marker of a read; the metric; the audit event for customer data."""
    t = telemetry.get()
    if span is None:
        return
    span.set_attribute(c.TOOL_STATUS, result.code)
    if not result.ok:
        span.set_status(Status(StatusCode.ERROR, result.code))
        span.set_attribute(c.ERROR_TYPE, result.code)
        if result.code.startswith("service_"):
            telemetry.clock().advance(10.0 if "timeout" in result.code else 0.2)   # the simulated wait
    run = current()
    marker = injection_in(run, name, arguments, result) if run else None
    if marker:
        span.set_attribute(c.INJECTION, True)
        span.set_attribute(c.INJECTION_ASK, marker)
    t.tool_calls.add(1, {c.TOOL_NAME: name, c.TOOL_KIND: "read", c.TOOL_STATUS: result.code})
    if name in CUSTOMER_DATA and run:
        subject = {"order_id": arguments.get("order_id")} if isinstance(arguments, dict) and arguments.get("order_id") else {}
        audit("data_access", agent_actor(), {"tool": name, "status": result.code,
                                             "orders": sorted(result.order_ids)[:10]}, subject=subject)


def injection_in(run: Run, name: str, arguments, result) -> str | None:
    """The practice data marks the orders, passages and tickets that carry an injected instruction."""
    if not result.ok or not run.injection:
        return None
    markers = run.injection
    if name == "get_order":
        return markers.get("orders", {}).get(result.order_ids[0] if result.order_ids else "")
    if name == "search_policy" and isinstance(result.data, list):
        for p in result.data:
            ask = markers.get("passages", {}).get(p.get("passage_id"))
            if ask:
                return ask
    return None


# ------------------------------------------------------------------ writes

def write_attributes(action, op_id: str, call_id: str, attempt: int) -> dict:
    a = {c.ORDER_ID: action.order_id, c.OPERATION_ID: op_id, c.IDEMPOTENCY_KEY: call_id, c.ATTEMPT: attempt}
    if action.tool == "request_refund":
        a.update({c.REFUND_AMOUNT: round(action.amount, 2), c.REFUND_REASON: action.reason_code})
    elif action.tool == "reship_item":
        a.update({c.SKU: action.sku, c.QUANTITY: action.quantity})
    else:
        a.update({c.SKU: action.sku, "larkfield.label.reason": action.reason})
    return a


def write_effect(action) -> dict:
    """The change itself, as codes and numbers (a label's `reason` is a code: it becomes label_reason)."""
    d = action.model_dump()
    if "reason" in d:
        d["label_reason"] = d.pop("reason")
    return {k: v for k, v in d.items() if v is not None}


def write_done(span, action, op_id: str, call_id: str, attempt: int, outcome: str, approval_event: str = "",
               error: str = "") -> None:
    t = telemetry.get()
    if span is not None:
        span.set_attribute(c.WRITE_OUTCOME, outcome)
        if outcome in ("timeout", "unavailable", "refused", "failed") or outcome.startswith("service"):
            span.set_status(Status(StatusCode.ERROR, outcome))
            span.set_attribute(c.ERROR_TYPE, outcome)
        if outcome == "timeout":
            telemetry.clock().advance(10.0)
    t.writes.add(1, {c.TOOL_NAME: action.tool, c.WRITE_OUTCOME: outcome})
    t.tool_calls.add(1, {c.TOOL_NAME: action.tool, c.TOOL_KIND: "write", c.TOOL_STATUS: outcome})
    audit("write", SYSTEM, {"tool": action.tool, "effect": write_effect(action), "operation_id": op_id,
                            "idempotency_key": call_id, "attempt": attempt, "outcome": outcome},
          subject={"order_id": action.order_id}, authority={"approval_event_id": approval_event})


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
    span.set_attributes(telemetry.clean({c.COST: round(u.cost_usd, 8) if u.cost_usd is not None else None,
                                         c.PRICE_TABLE: PRICES_CHECKED}))
    if state.stop_reason and state.stop_reason != "finished":
        span.set_attribute(c.ERROR_TYPE, state.stop_reason)
        if state.stop_reason in ("provider_error", "no_recording", "too_many_errors", "max_steps", "repeated_call",
                                 "time", "cost"):
            span.set_status(Status(StatusCode.ERROR, state.stop_reason))
    if p is not None:
        from .approval import required_role
        actions = [write_effect(a) for a in p.actions]
        evidence = sorted({f"order:{o}" for o in state.seen_orders()} |
                          {f"passage:{x.get('passage_id')}" for e in state.evidence if e.ok and e.tool == "search_policy"
                           and isinstance(e.data, list) for x in e.data if isinstance(x, dict)})
        eid = audit("proposal", agent_actor(state.model), {"outcome": p.outcome, "rule": p.rule, "actions": actions,
                                                            "design": state.variant},
                    authority={"needs_role": required_role(state) if p.actions else ""}, evidence=evidence[:20])
        state.telemetry["proposal_event"] = eid


@contextlib.contextmanager
def agent_span(name: str, model: str, parent_message: dict | None = None):
    """One worker of the two-worker design: `invoke_agent investigator` or `invoke_agent resolver`.

    With `parent_message` (a handoff), the span's parent is the context IN THE MESSAGE, as in a second
    process: a message without a traceparent starts a new trace, and the run is no longer one story."""
    t = telemetry.get()
    if not t.enabled:
        yield None
        return
    attrs = {c.OPERATION: c.OP_AGENT, c.AGENT_NAME: name, c.AGENT_ID: f"{AGENT_ID}/{name}", c.REQUEST_MODEL: model}
    if parent_message is None:
        with t.span(f"invoke_agent {name}", attrs) as span:
            yield span
        return
    from opentelemetry import context as otel_context
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    carrier = {"traceparent": parent_message["traceparent"]} if parent_message.get("traceparent") else {}
    ctx = TraceContextTextMapPropagator().extract(carrier, context=otel_context.Context())
    attrs.update({c.HANDOFF_FROM: parent_message.get("from"), c.HANDOFF_TO: parent_message.get("to"),
                  c.HANDOFF_ITEMS: parent_message.get("report_items"),
                  "larkfield.handoff.context": "propagated" if carrier else "missing",
                  **({} if carrier else run_attributes(current()) if current() else {})})
    token = otel_context.attach(ctx)
    try:
        with t.span(f"invoke_agent {name}", attrs) as span:
            yield span
    finally:
        otel_context.detach(token)
