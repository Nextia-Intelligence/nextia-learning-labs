"""The replayed week: a week of Larkfield's tickets through the live workflow, with its telemetry.

    python -m scenarios week --out work/week            the week of the course (with the practice incidents)
    python -m scenarios week --healthy --out work/healthy   the same tickets on the healthy release, no incident
    python -m scenarios week --otlp                     also send everything to a Collector (OTLP/HTTP), paced

Every model decision is a real recording of the agents course, replayed (the mock provider). The traffic is
constructed: which ticket arrives when, the releases, the people's approval times and the practice incidents
("a practice incident we caused on purpose"). Each run uses a fresh copy of the practice database.

Time. The week is Monday 12 to Sunday 18 October 2026, Toronto time, about 45 tickets a day (the agents
course's help desk). In the files, every span has its practice time (an approval that waits all night shows a
15-hour gap). With --otlp the week is replayed in compressed time (--speed, default 1,000: a practice day
lasts 86 seconds) so that Grafana's alert windows can see it; then the spans have the real time of the replay.
The workflow's date rules keep the agents course's "today" (9 October 2026), so that the recordings replay
exactly; lessons never compute dates from the week's timestamps.
"""

import gzip
import json
import random
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from resolver import conventions as c  # noqa: E402
from resolver import live, observe, telemetry  # noqa: E402
from resolver.approval import required_role  # noqa: E402
from resolver.data import SEED_DB, load_tasks  # noqa: E402
from resolver.evaluate import score  # noqa: E402
from resolver.loop import Limits  # noqa: E402
from resolver.providers import MockProvider  # noqa: E402
from resolver.runner import new_state  # noqa: E402
from resolver.systems import Faults, World  # noqa: E402

TZ = timezone(timedelta(hours=-4))           # Toronto in October (EDT)
START = datetime(2026, 10, 12, tzinfo=TZ)    # Monday
DAYS = 7
PER_DAY = {0: 52, 1: 52, 2: 52, 3: 52, 4: 52, 5: 28, 6: 28}   # 316 tickets: about 45 a day
SEED = 31
APPROVER = {"agent": "usr-sam", "team_lead": "usr-camille", "grace": "usr-grace"}
REVIEW_SHARE = 0.2                           # Priya reviews one run in five
CAPTURE = telemetry.CONTENT                  # OBS_CAPTURE_CONTENT=on: text on the model spans (the redaction exercise)


def at(day: int, hh: int, mm: int = 0) -> datetime:
    return START + timedelta(days=day, hours=hh, minutes=mm)


@dataclass
class Plan:
    """What happens in the week: releases, incidents and fixed tickets (all constructed; the decisions are real)."""
    name: str
    releases: list = field(default_factory=list)       # (from, Release)
    incidents: list = field(default_factory=list)      # (from, to, tool, mode, what)
    local_trial: tuple | None = None                   # (from, to, share): tickets sent to gemma3:4b
    fixed: list = field(default_factory=list)          # (when, task_id, why)


def course_week() -> Plan:
    r200 = live.Release("2.0.0", "safe", "person", "")
    r210 = live.Release("2.1.0", "naive", "close", "chat-strong")
    r211 = live.Release("2.1.1", "safe", "person", "chat-strong")
    return Plan(
        name="week",
        releases=[(at(0, 0), r200), (at(2, 9), r210), (at(4, 11, 30), r211)],
        incidents=[(at(3, 8, 30), at(3, 9, 30), "request_refund", "timeout_after_write",
                    "the payment service is slow: the first call of each refund answers after the 10-second "
                    "timeout, but the refund is made"),
                   (at(3, 12, 30), at(3, 15, 30), "send_reply", "unavailable", "the help desk's reply service is down")],
        local_trial=(at(5, 0), at(7, 0), 0.3),
        fixed=[(at(2, 17, 52), "T-90104", "the double refund: proposed in the evening, approved the next morning"),
               (at(0, 10, 14), "T-90501", "an injected instruction in a courier note"),
               (at(3, 11, 5), "T-90501", "the same, on the strong model"),
               (at(1, 14, 31), "T-90504", "an injected instruction in a gift message"),
               (at(4, 15, 2), "T-64856", "an injected instruction in a policy passage"),
               (at(5, 10, 40), "T-64872", "the local model's repeated call", "gemma3:4b"),
               (at(6, 11, 15), "T-90602", "the payment service is down; the local model's confident reply",
                "gemma3:4b")])


def candidate_week() -> Plan:
    """The final assignment's week: a new release on Larkfield's tickets. Read it as an operator would: from the
    telemetry, not from this list."""
    def rel(version, retry="safe", context="on", capture="off"):
        return live.Release(version, retry, "person", "chat-strong", context, capture)
    return Plan(
        name="candidate-week",
        releases=[(at(0, 0), rel("2.2.0-rc1")), (at(1, 12), rel("2.2.0-rc2", context="off")),
                  (at(2, 14), rel("2.2.1-rc1", retry="naive", context="off")),
                  (at(4, 9), rel("2.2.2-rc1", capture="on"))],
        incidents=[(at(2, 15), at(2, 18), "request_refund", "timeout_after_write", "the payment service is slow"),
                   (at(3, 8, 30), at(3, 12), "request_refund", "timeout_after_write", "the payment service is slow"),
                   (at(5, 10), at(5, 13), "get_payments", "unavailable", "the payment service is down")],
        local_trial=(at(3, 0), at(5, 0), 0.25),
        fixed=[])


def healthy_week() -> Plan:
    return Plan(name="healthy-week", releases=[(at(0, 0), live.Release("2.0.0", "safe", "person", ""))],
                fixed=course_week().fixed)


# ------------------------------------------------------------------ the schedule

def arrivals(rng: random.Random, plan: Plan, tasks: list[str]) -> list[tuple[datetime, str]]:
    """Ticket arrivals: mostly in the day (07:00-22:00), a few at night; tasks drawn evenly."""
    out = []
    for day in range(DAYS):
        n = PER_DAY[day] - sum(1 for f in plan.fixed if (f[0] - START).days == day)
        for _ in range(n):
            minute = int(rng.triangular(7 * 60, 22 * 60, 13 * 60)) if rng.random() > 0.08 else rng.randrange(0, 7 * 60)
            out.append((at(day, 0) + timedelta(minutes=minute, seconds=rng.randrange(60)), rng.choice(tasks)))
    out += [(f[0], f[1]) for f in plan.fixed]
    return sorted(out)


def approval_time(rng: random.Random, proposed: datetime) -> datetime:
    """When a person decides: in staffed hours (weekdays 08:30-17:30, weekends 10:00-16:00), a few minutes to an
    hour after the proposal; outside them, the next staffed morning."""
    t = proposed
    for _ in range(4):
        wd = t.weekday()
        open_, close_ = ((8, 30), (17, 30)) if wd < 5 else ((10, 0), (16, 0))
        start = t.replace(hour=open_[0], minute=open_[1], second=0, microsecond=0)
        end = t.replace(hour=close_[0], minute=close_[1], second=0, microsecond=0)
        if t < start:
            return start + timedelta(minutes=rng.randrange(5, 60), seconds=rng.randrange(60))
        if t < end - timedelta(minutes=10):
            return t + timedelta(minutes=rng.randrange(4, 45), seconds=rng.randrange(60))
        t = (t + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return t


def release_at(plan: Plan, when: datetime) -> live.Release:
    current = plan.releases[0][1]
    for start, r in plan.releases:
        if when >= start:
            current = r
    return current


def incident_faults(plan: Plan, when: datetime, tool: str) -> list[dict]:
    """The incidents' simulated failures at this time: the first call of the tool fails (once per run)."""
    return [{"tool": t, "mode": m, "times": 1} for a, b, t, m, _ in plan.incidents if a <= when < b and t == tool]


def ns(d: datetime) -> int:
    return int(d.timestamp() * 1e9)


# ------------------------------------------------------------------ the week

class Week:
    def __init__(self, plan: Plan, out: Path, otlp: bool = False, speed: float = 1000.0, seed: int = SEED,
                 truth_path: Path | None = None):
        self.plan, self.out, self.otlp, self.speed, self.truth_path = plan, out, otlp, speed, truth_path
        self.rng = random.Random(seed)
        self.tasks = load_tasks()
        self.provider = MockProvider()
        self.tmp = Path(tempfile.mkdtemp(prefix="week-"))
        out.mkdir(parents=True, exist_ok=True)
        for name in ("traces.jsonl", "logs.jsonl", "metrics.jsonl", "audit.jsonl", "audit.anchor.json", "audit.keys.json",
                     "workflow.log", "truth.json", "plan.json"):
            (out / name).unlink(missing_ok=True)
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader
        self.reader = InMemoryMetricReader()
        export = "file,otlp" if otlp else "file"
        telemetry.seed_ids(seed)
        self.t = telemetry.Telemetry(export=export, folder=out, audit_path=out / "audit.jsonl", metric_reader=self.reader,
                                     id_generator=None if otlp else telemetry.SeededIds(seed), key_seed=f"practice-{seed}")
        self.old = telemetry.use(self.t)
        live.LOG["path"] = out / "workflow.log"      # Amira's log of the week (one line per closed ticket)
        self.real_start = time.time_ns()
        self.truth: list[dict] = []
        self.metrics_out = telemetry._Lines(out / "metrics.jsonl")

    def when_ns(self, d: datetime) -> int:
        """Span time: the practice time in the files; with --otlp the compressed time of the replay."""
        if not self.otlp:
            return ns(d)
        return self.real_start + int((ns(d) - ns(START)) / self.speed)

    def wait_until(self, d: datetime) -> None:
        if self.otlp:
            delay = (self.when_ns(d) - time.time_ns()) / 1e9
            if delay > 0:
                time.sleep(delay)

    def snapshot(self, hour_end: datetime) -> None:
        """One cumulative metrics snapshot per practice hour, with the hour's time on every point."""
        from opentelemetry.exporter.otlp.proto.common.metrics_encoder import encode_metrics
        data = self.reader.get_metrics_data()
        if data is None:
            return
        obj = telemetry.otlp_json(encode_metrics(data))
        stamp, origin = str(self.when_ns(hour_end)), str(self.when_ns(START))

        def fix(node):
            if isinstance(node, dict):
                for k in list(node):
                    if k == "timeUnixNano" and "exemplars" not in k:
                        node[k] = stamp
                    elif k == "startTimeUnixNano":
                        node[k] = origin
                    else:
                        fix(node[k])
            elif isinstance(node, list):
                for x in node:
                    fix(x)
        fix(obj)
        self.metrics_out.write(obj)

    def run(self) -> dict:
        events = [(when, 0, "ticket", task_id, None) for when, task_id in arrivals(self.rng, self.plan, sorted(self.tasks))]
        seq = {}
        next_hour = START + timedelta(hours=1)
        pending = []
        import heapq
        heap = []
        for i, e in enumerate(events):
            heapq.heappush(heap, (e[0], e[1], i, e))
        n = len(events)
        while heap:
            when, prio, _, (_, _, kind, task_id, payload) = heapq.heappop(heap)
            while when >= next_hour:
                self.snapshot(next_hour)
                next_hour += timedelta(hours=1)
            self.wait_until(when)
            if kind == "ticket":
                day = (when - START).days
                seq[day] = seq.get(day, 0) + 1
                run_id = f"R-{when.strftime('%m%d')}-{seq[day]:03d}"
                state, world, release = self.start(run_id, task_id, when)
                if state.status == "waiting_approval":
                    # the run's own steps take their recorded time, also in compressed replays
                    proposed = when + timedelta(seconds=(state.telemetry["proposed_ns"] - self.when_ns(when)) / 1e9)
                    decide_at = approval_time(self.rng, proposed)
                    n += 1
                    heapq.heappush(heap, (decide_at, 1, n, (decide_at, 1, "decide", task_id, (state, world))))
                else:
                    self.finish(state, world, when)
            else:
                state, world = payload
                self.decide(state, world, when)
        self.snapshot(next_hour)
        self.t.flush()
        self.t.shutdown()
        telemetry.use(self.old)
        telemetry.seed_ids(None)
        live.LOG["path"] = None
        shutil.rmtree(self.tmp, ignore_errors=True)
        return self.summary()

    # -------------------------------------------------------------- one ticket
    def start(self, run_id: str, task_id: str, when: datetime):
        task = self.tasks[task_id]
        release = release_at(self.plan, when)
        variant, model = live.choose(task, "agent", "chat-small", release)
        local = self.plan.local_trial
        forced = next((f[3] for f in self.plan.fixed if f[0] == when and f[1] == task_id and len(f) > 3), None)
        if local and local[0] <= when < local[1] and (forced == "gemma3:4b" or self.rng.random() < local[2]):
            variant, model = "agent_structured", "gemma3:4b"
        db = self.tmp / f"{run_id}.sqlite"
        shutil.copyfile(SEED_DB, db)
        faults = [*task.faults, *incident_faults(self.plan, when, "send_reply")]
        world = World(db, task.task_id, Faults(faults))
        state = new_state(task, variant, model, run_id)
        telemetry.CONTENT = CAPTURE or getattr(release, "capture", "off") == "on"
        with telemetry.run_clock(self.when_ns(when)):
            state = live.start(task, variant, model, self.provider.complete, world, Limits(), state=state,
                               release=release)
        telemetry.CONTENT = CAPTURE
        state.telemetry["release"] = release.version
        state.telemetry["arrived"] = when.isoformat()
        return state, world, release

    def decide(self, state, world, when: datetime):
        task = self.tasks[state.task_id]
        release = release_at(self.plan, when)
        role = required_role(state)
        left = {k: v for k, v in world.faults.left.items() if k[0] != "send_reply"}   # the task's own, unused
        faults = Faults([*incident_faults(self.plan, when, "request_refund"), *incident_faults(self.plan, when, "send_reply")])
        for k, v in left.items():
            faults.left.setdefault(k, v)
        world.faults = faults
        with telemetry.run_clock(self.when_ns(when)):
            live.decide(state, task, True, APPROVER[role], role, world, release=release)
        self.finish(state, world, when, decided=when)

    def finish(self, state, world, when: datetime, decided: datetime | None = None):
        task = self.tasks[state.task_id]
        s = score(task, state, world.changes())
        changes = world.changes()
        effects = {}
        for ch in changes:
            key = (ch["tool"], ch["order_id"], ch.get("amount"), ch.get("sku"), ch.get("quantity"))
            effects[key] = effects.get(key, 0) + 1
        duplicates = sum(n - 1 for n in effects.values() if n > 1)
        calls = [(e.tool, ",".join(sorted(e.arguments))) for e in state.evidence]
        loop = max((calls.count(x) for x in set(calls)), default=0) >= 3 or state.stop_reason == "repeated_call"
        tool_error = [e for e in state.evidence if not e.ok and e.code.startswith("service_")]
        outcome = state.telemetry.get("outcome", "")
        truth = {
            "run_id": state.run_id, "ticket": state.task_id, "slice": task.slice, "model": state.model,
            "design": state.variant, "release": state.telemetry.get("release"), "outcome": outcome,
            "success": s.success, "expected": task.expected["outcome"],
            "arrived": state.telemetry.get("arrived"), "decided": decided.isoformat() if decided else None,
            "language": observe.language_of(task.text), "hard": live.is_hard(task.text),
            "duplicate_refunds": duplicates,
            "scenarios": [x for x, on in [
                ("double_refund", duplicates > 0),
                ("loop", loop),
                ("hidden_tool_error", bool(tool_error) and outcome == "resolved" and not s.success),
                ("no_action", outcome == "resolved" and state.telemetry.get("reply") == "failed"
                 and not any(o.status == "done" for o in state.operations)),
                ("injection_seen", state.task_id in ("T-90501", "T-90504", "T-64856", "T-80002", "T-90505")),
                ("model_switch", state.model == "chat-strong"),
                ("local_model", state.model == "gemma3:4b"),
                ("overnight_approval", bool(decided) and
                 decided - datetime.fromisoformat(state.telemetry["arrived"]) > timedelta(hours=8)),
                ("non_english", observe.language_of(task.text) != "en"),
            ] if on],
        }
        self.truth.append(truth)
        if self._review(state.run_id):
            self.review(state, s.success, when)

    def _review(self, run_id: str) -> bool:
        import hashlib
        return int(hashlib.sha256(run_id.encode()).hexdigest(), 16) % 100 < REVIEW_SHARE * 100

    def review(self, state, success: bool, when: datetime):
        """Priya's sampled review (simulated: the agents course's labels stand in for her judgement),
        attached to the run's trace as a GenAI evaluation event, one practice day later."""
        from opentelemetry import trace
        from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
        ref = state.telemetry.get("root")
        if not ref:
            return
        ctx = trace.set_span_in_context(NonRecordingSpan(SpanContext(int(ref["trace_id"], 16), int(ref["span_id"], 16),
                                                                     False, TraceFlags(1))))
        from opentelemetry import context as otel_context
        token = otel_context.attach(ctx)
        try:
            with telemetry.run_clock(self.when_ns(when + timedelta(days=1))):
                self.t.event("gen_ai.evaluation.result", {
                    "gen_ai.evaluation.name": "sampled-review", "gen_ai.evaluation.score.value": 1.0 if success else 0.0,
                    "gen_ai.evaluation.score.label": "pass" if success else "fail", c.RUN_ID: state.run_id,
                    c.TICKET_ID: state.task_id, "larkfield.reviewer": "usr-priya"})
        finally:
            otel_context.detach(token)

    def summary(self) -> dict:
        truth = self.truth_path or (None if self.plan.name == "candidate-week" else self.out / "truth.json")
        if truth:   # the candidate week's truth is the answer key: written only where the course team asks
            Path(truth).write_text(json.dumps({"plan": self.plan.name, "runs": self.truth}, indent=0) + "\n")
        plan = {"name": self.plan.name, "week": [START.isoformat(), (START + timedelta(days=DAYS)).isoformat()],
                "releases": [{"from": w.isoformat(), "version": r.version, "retry": r.retry,
                              "reply_failure": r.reply_failure, "hard_model": r.hard_model}
                             for w, r in self.plan.releases],
                "incidents": [{"from": a.isoformat(), "to": b.isoformat(), "tool": t, "mode": m, "what": w}
                              for a, b, t, m, w in self.plan.incidents],
                "local_trial": [self.plan.local_trial[0].isoformat(), self.plan.local_trial[1].isoformat(),
                                self.plan.local_trial[2]] if self.plan.local_trial else None,
                "fixed": [{"at": f[0].isoformat(), "ticket": f[1], "why": f[2], **({"model": f[3]} if len(f) > 3 else {})}
                          for f in self.plan.fixed],
                "compressed": {"speed": self.speed} if self.otlp else None}
        if self.plan.name != "candidate-week":
            (self.out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n")
        elif self.truth_path:
            Path(self.truth_path).with_name("candidate-plan.json").write_text(json.dumps(plan, indent=1) + "\n")
        counts = {}
        for t in self.truth:
            for s in t["scenarios"]:
                counts[s] = counts.get(s, 0) + 1
        return {"runs": len(self.truth), "scenarios": counts,
                "resolved": sum(1 for t in self.truth if t["outcome"] == "resolved"),
                "success": sum(1 for t in self.truth if t["success"])}


def compress(folder: Path) -> None:
    """gzip the telemetry files (the saved data for labs)."""
    for name in ("traces.jsonl", "logs.jsonl", "metrics.jsonl"):
        p = folder / name
        if p.exists():
            with p.open("rb") as f, gzip.GzipFile(filename=str(folder / (name + ".gz")), mode="wb", compresslevel=9, mtime=0) as g:
                shutil.copyfileobj(f, g)
            p.unlink()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="python -m scenarios week")
    ap.add_argument("--out", default=str(PROJECT / "work" / "week"))
    ap.add_argument("--healthy", action="store_true", help="the same tickets on the healthy release, no incident")
    ap.add_argument("--candidate", action="store_true", help="the final assignment's week: a new release candidate")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--truth", help="where to write the scenario truth (the course team's answer key)")
    ap.add_argument("--otlp", action="store_true", help="also send to a Collector (OTLP/HTTP), in compressed time")
    ap.add_argument("--speed", type=float, default=1000.0)
    ap.add_argument("--gzip", action="store_true", help="compress the files (as in data/telemetry/)")
    args = ap.parse_args(argv)
    plan = healthy_week() if args.healthy else candidate_week() if args.candidate else course_week()
    out = Path(args.out)
    started = time.time()
    summary = Week(plan, out, args.otlp, args.speed, seed=3131 if args.candidate and args.seed == SEED else args.seed,
                   truth_path=Path(args.truth) if args.truth else None).run()
    if args.gzip:
        compress(out)
    print(f"{plan.name}: {summary['runs']} runs in {time.time() - started:.0f} s -> {out}")
    print(f"resolved {summary['resolved']}, right by the course's labels {summary['success']}")
    if plan.name != "candidate-week" or args.truth:
        print("scenario runs: " + ", ".join(f"{k} {v}" for k, v in sorted(summary["scenarios"].items())))


if __name__ == "__main__":
    main()
