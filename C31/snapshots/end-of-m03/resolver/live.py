"""The live workflow: a ticket from start to close, as it runs at Larkfield every day.

    start()    the run (the agents course's designs) until a proposal. A proposal with changes waits for a
               person; a reply or a question is sent at once.
    decide()   minutes or hours later: a person approves or rejects; then the approved writes run (operation
               IDs, retries, reconcile) and the reply is sent.
    close()    the ticket's final outcome, and one log line (work/logs/workflow.log).

Traces: start() is trace 1; it ends with an `approval.request` span. decide() is trace 2: it starts with a
LINK to trace 1's approval request and records who decided, their role and limit, and how long the run waited.
Why two traces: an approval can wait all night. A span that stays open for 15 hours is lost if the process
restarts, and a trace that lasts a day is hard to read. So the wait is an attribute and a metric
(larkfield.approval.wait_s), and the link joins the two traces into one story.

Release settings (environment variables, read by Release.from_env):
    RESOLVER_RETRY=safe|naive          naive: a timed-out write is sent again with a new ID (the double refund)
    RESOLVER_REPLY_FAILURE=person|close    close: a failed reply still closes the ticket as resolved (a bug)
    RESOLVER_HARD_MODEL=chat-strong    hard tickets go to the structured agent on this model (Omar's switch)
"""

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from opentelemetry.trace import Status, StatusCode

from . import conventions as c
from . import helpdesk
from . import observe, telemetry
from .approval import LIMITS, ApprovalError, decide as approval_decide, required_role
from .data import WORK
from .execute import ExecutionRefused, Interrupted, execute
from .runner import new_state, run_task
from .systems import ServiceError

VERSION = "2.0.0"
OUTCOMES = {"reply_only": "resolved", "ask_customer": "asked_customer", "hand_to_person": "handed_to_person"}
PEOPLE = {"sam": "usr-sam", "camille": "usr-camille", "grace": "usr-grace", "amira": "usr-amira"}


@dataclass(frozen=True)
class Release:
    version: str = VERSION
    retry: str = "safe"
    reply_failure: str = "person"
    hard_model: str = ""
    approval_context: str = "on"   # off: the decision runs without the run's context (no link, no run ID)
    capture: str = "off"           # on: prompt text on the model spans (OBS_CAPTURE_CONTENT)

    @classmethod
    def from_env(cls) -> "Release":
        return cls(version=os.environ.get("OBS_RELEASE", VERSION),
                   retry=os.environ.get("RESOLVER_RETRY", "safe"),
                   reply_failure=os.environ.get("RESOLVER_REPLY_FAILURE", "person"),
                   hard_model=os.environ.get("RESOLVER_HARD_MODEL", ""),
                   approval_context=os.environ.get("RESOLVER_APPROVAL_CONTEXT", "on"),
                   capture=os.environ.get("OBS_CAPTURE_CONTENT", "off"))


def is_hard(text: str) -> bool:
    """Omar's rule for a "hard" ticket: a late or missing delivery (the fixed workflow's keyword lists), two or
    more order numbers, or more than 60 words. These are the tickets where the small model asked the customer
    "a replacement or a refund?" instead of refunding the late fee (the agents course's recordings)."""
    from .workflow import keyword_kind
    rule, kind = keyword_kind(text)
    return kind in ("late", "missing_box") or len(set(re.findall(r"LK-\d{6}", text))) >= 2 or len(text.split()) > 60


def choose(task, variant: str, model: str, release: Release) -> tuple[str, str]:
    if release.hard_model and is_hard(task.text):
        return "agent_structured", release.hard_model
    return variant, model


def person_id(name: str | None, role: str) -> str:
    if name and name.startswith("usr-"):
        return name
    if not name:
        return {"agent": "usr-sam", "team_lead": "usr-camille", "grace": "usr-grace"}[role]
    return PEOPLE.get(name.lower(), "usr-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"))


def now_ns() -> int:
    return telemetry.clock().now()


def limit(role: str) -> float:
    return LIMITS[role] if LIMITS[role] != float("inf") else -1


# ------------------------------------------------------------------ trace 1

def start(task, variant: str, model: str, complete, world, limits, *, run_id: str | None = None,
          release: Release | None = None, on_step=None, state=None):
    """Run a ticket until it waits for approval or is closed. Returns the state."""
    release = release or Release.from_env()
    state = state or new_state(task, variant, model, run_id)
    state.telemetry["release"] = release.version
    run = observe.new_run(task, state, release.version)

    def then(st):
        t = telemetry.get()
        if st.status == "waiting_approval":
            need = required_role(st)
            # The last span of trace 1: what waits, and for whom. Trace 2 links to it.
            with t.span("approval.request", {c.APPROVAL_LIMIT: limit(need), "larkfield.approval.needs_role": need,
                                             c.ACTIONS: len(st.proposal.actions)}) as span:
                if span is not None:
                    st.telemetry["approval_request"] = telemetry.span_ref(span)
            st.telemetry["proposed_ns"] = now_ns()
        elif st.status == "done":
            _reply_and_close(st, world, release, OUTCOMES.get(st.proposal.outcome, "resolved"))
        else:
            close(st, "handed_to_person", reason=st.stop_reason or (st.proposal.rule if st.proposal else ""))

    with observe.run_context(run):
        state = run_task(task, state.variant, state.model, complete, world, limits, state, on_step, then=then)
    return state


# ------------------------------------------------------------------ trace 2

def decide(state, task, approve: bool, approver: str | None, role: str, world, *, note: str = "",
           release: Release | None = None, interrupt: str = "", save=lambda s: None):
    """A person's decision on a waiting run, then the writes and the reply. Raises ApprovalError if refused."""
    release = release or Release.from_env()
    who = person_id(approver, role)
    proposed = state.telemetry.get("proposed_ns")
    if proposed and telemetry.clock().now() < proposed:
        # The first trace's clock ran ahead of the wall clock by the recorded model time: start after it.
        telemetry.clock().ns = proposed
    wait_s = round((now_ns() - proposed) / 1e9, 1) if proposed else None
    state.telemetry["wait_s"] = wait_s
    t = telemetry.get()
    run = observe.new_run(task, state, release.version)
    links = telemetry.link_to(state.telemetry.get("approval_request"), **{"larkfield.link": "approval of this run"})
    attrs = {**observe.run_attributes(run), c.APPROVER: who, c.APPROVER_ROLE: role, c.APPROVAL_LIMIT: limit(role),
             c.APPROVAL_WAIT: wait_s, c.OPERATION: "approve"}
    context = observe.run_context(run)
    if release.approval_context == "off":   # a decision handled by a job that does not know the run
        import contextlib
        links, context = [], contextlib.nullcontext()
        attrs = {k: v for k, v in attrs.items() if k not in (c.RUN_ID, c.CUSTOMER_ID, c.APPROVAL_WAIT)}
    with context, t.span(f"approve {observe.WORKFLOW}", attrs, links=links) as span:
        _decide(state, task, approve, who, role, world, note, release, interrupt, save, wait_s, span)
    return state


def _decide(state, task, approve, who, role, world, note, release, interrupt, save, wait_s, span):
    try:
        approval_decide(state, approve, who, role, note)
    except ApprovalError:
        if span is not None:
            span.set_attribute(c.APPROVAL_DECISION, "refused_by_rules")
            span.set_status(Status(StatusCode.ERROR, "approval_refused"))
        raise
    decision = state.approval.decision
    if span is not None:
        span.set_attribute(c.APPROVAL_DECISION, decision)
    if wait_s is not None:
        telemetry.get().approval_wait.record(wait_s, {c.APPROVER_ROLE: role, c.APPROVAL_DECISION: decision})
    eid = ""
    if not approve:
        close(state, "handed_to_person", reason="rejected")
        save(state)
        return
    try:
        execute(state, world, save, naive=release.retry == "naive", interrupt=interrupt, approval_event=eid)
    except (Interrupted, ExecutionRefused):
        raise
    if state.status == "done":
        _reply_and_close(state, world, release, "resolved")
    else:
        close(state, "handed_to_person", reason="write_failed")
    save(state)


# ------------------------------------------------------------------ the reply and the close

def _reply_and_close(state, world, release: Release, outcome: str) -> None:
    status = _send(state, world)
    state.telemetry["reply"] = status
    if status == "failed":
        if release.reply_failure != "close":
            close(state, "handed_to_person", reason="reply_failed")
            return
    close(state, outcome)


def _send(state, world) -> str:
    """Send the reply to the customer (a mock help desk). 'sent' or 'failed'."""
    run = observe.current()
    with observe.tool_span("send_reply", {"ticket_id": state.task_id}, kind="write") as span:
        try:
            helpdesk.send_reply(world, state.run_id, state.proposal.reply, run.language if run else "")
            status = "sent"
        except ServiceError as e:
            status = "failed"
            if span is not None:
                span.set_status(Status(StatusCode.ERROR, e.code))
                span.set_attribute(c.ERROR_TYPE, e.code)
        if span is not None:
            span.set_attribute(c.REPLY_STATUS, status)
            span.set_attribute(c.TOOL_STATUS, "ok" if status == "sent" else "service_unavailable")
    telemetry.get().tool_calls.add(1, {c.TOOL_NAME: "send_reply", c.TOOL_KIND: "write", c.TOOL_STATUS: status})
    return status


def close(state, outcome: str, reason: str = "") -> None:
    """The final outcome of the ticket: the help desk's status and one log line (Amira's log, as it was before
    this course). From Module 2 on also one metric point; later one event and audit events."""
    state.telemetry["outcome"] = outcome
    world_status = {"resolved": "resolved", "asked_customer": "waiting_customer"}.get(outcome, "with_person")
    state.status = {"resolved": "done", "asked_customer": "done"}.get(outcome, "handed_to_person")
    writes = sum(1 for o in state.operations if o.status == "done")
    log_line(state, outcome, writes)
    t = telemetry.get()
    run = observe.current()
    labels = {c.OUTCOME: outcome, c.REQUEST_MODEL: state.model, c.LANGUAGE: run.language if run else "",
              c.RELEASE: run.release if run else "", c.VARIANT: state.variant}
    t.runs.add(1, labels)
    attrs = {c.RUN_ID: run.run_id if run else None, c.TICKET_ID: state.task_id, c.OUTCOME: outcome,
             "larkfield.reason": reason or None,
             "larkfield.writes_done": writes, "larkfield.reply": state.telemetry.get("reply"),
             "larkfield.helpdesk.status": world_status}
    from opentelemetry import trace
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attributes(telemetry.clean(attrs))
    state.telemetry["closed"] = True


LOG = {"path": None}   # the replayed week writes its own log


def log_line(state, outcome: str, writes: int) -> None:
    """Amira's log: one line per closed ticket (what Larkfield had before this course)."""
    path = Path(LOG["path"] or os.environ.get("RESOLVER_LOG", WORK / "logs" / "workflow.log"))
    path.parent.mkdir(parents=True, exist_ok=True)
    tz = timezone(timedelta(hours=float(os.environ.get("OBS_TZ_OFFSET", "-4"))))   # Larkfield: Toronto
    when = datetime.fromtimestamp(now_ns() / 1e9, tz).isoformat(timespec="seconds")
    reply = state.telemetry.get("reply", "-")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{when} INFO ticket={state.task_id} run={state.run_id} model={state.model} status={outcome} "
                f"writes={writes} reply={reply}\n")
