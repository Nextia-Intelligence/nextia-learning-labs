"""The worker: takes queued jobs and does their AI work (the scaling course, Module 4).

    python -m ticket_api.worker                 run until Ctrl+C
    python -m ticket_api.worker --once          take what is queued now, then stop
    python -m ticket_api.worker --concurrency 8 up to 8 jobs at the same time

One job = the AI work of one ticket, in two steps (triage: the help desk's assistant, then
embed). Each step's result is saved as soon as it is made, with the job's ID: if the job is
delivered again (a worker stopped, its lease ended), the steps that are done are not called
again, and no result is saved twice.

Errors:
- the provider is over its quota (429): the job waits (the provider's hint or a growing
  backoff, whichever is longer) and does not lose an attempt: it is not the job's fault;
- the provider is down (5xx) or too slow (timeout): retry later, with exponential backoff
  and jitter, at most JOB_MAX_ATTEMPTS attempts; then the job is a dead letter, for a
  person to look at.
- the provider refused the request or gave an answer that is not valid: failed at once (the
  same request would fail again). An answer with no text (the model used all its tokens) is
  saved in ai_runs with status "error": it cost tokens, and it says why the job failed.
- the circuit breaker is open (Module 5): the job goes back to the queue until the circuit
  may close, and the attempt does not count.

Stopping (Module 5): on SIGTERM or Ctrl+C the worker takes no new job, lets the running ones
finish for up to WORKER_DRAIN_SECONDS, and gives the rest back to the queue (not counted
as an attempt). A worker that is killed (SIGKILL, a crash, a lost machine) cannot do this:
its jobs stay "running" until their lease ends, then another worker takes them again.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import socket
import sys
import time

import psycopg
from opentelemetry.trace import SpanKind, StatusCode

from ticket_api import ai, assistant, jobs, releases, repository, rollout, telemetry
from ticket_api.cache import Cache, make_cache
from ticket_api.config import Settings, SettingsError, load_settings
from ticket_api.db import Database
from ticket_api.intake import embed_cached, read_triage, run_record
from ticket_api.provider import (
    Provider,
    ProviderError,
    ProviderRateLimited,
    ProviderRejected,
    make_provider,
)
from ticket_api.resilience import BreakerOpen

logger = logging.getLogger("ticket_api.worker")


class Worker:
    def __init__(
        self,
        db: Database,
        provider: Provider,
        settings: Settings,
        cache: Cache | None = None,
        name: str | None = None,
    ):
        self.db = db
        self.provider = provider
        self.settings = settings
        self.cache = cache
        self.name = name or f"{socket.gethostname()}-{os.getpid()}"
        self.concurrency = settings.worker_concurrency
        self.in_flight: set[asyncio.Task] = set()
        self.rate_limited = 0  # 429 answers in a row (they make the next wait longer)
        self._breaker_seen = "closed"
        self.rollout = rollout.Watcher(db)  # Module 5: the release state (canary, shadow)
        self.counts = {
            "claimed": 0,
            "succeeded": 0,
            "retried": 0,
            "failed": 0,
            "dead_letter": 0,
            "waiting": 0,
            "released": 0,
        }

    # ----- database steps (the pool is synchronous: they run in a thread) -----

    def _claim(self, n: int) -> list[dict]:
        with telemetry.quiet(), self.db.connection() as conn:
            jobs.expired_without_attempts(conn)
            return jobs.claim(conn, self.name, n, self.settings.job_lease_seconds)

    def _load(self, job: dict) -> tuple[dict | None, dict]:
        with self.db.connection() as conn:
            return repository.ticket_for_work(conn, job["ticket_id"]), repository.job_runs(
                conn, job["job_id"]
            )

    def _save_step(self, job: dict, ticket: dict, run: dict, extra: dict) -> None:
        with self.db.connection() as conn:  # one short transaction per step
            if not repository.save_job_ai_run(conn, ticket["ticket_id"], job["job_id"], run):
                return  # this job saved this step before (a second delivery): nothing to add
            if run["task"] == "triage" and run["status"] == "ok":
                t = extra["triage"]
                repository.set_triage(conn, ticket["ticket_id"], t.team, t.needs_human)
            elif run["task"] == "embed":
                source = hashlib.sha256(f"{ticket['subject']}\n{ticket['body']}".encode())
                repository.save_embedding(
                    conn,
                    ticket["ticket_id"],
                    ai.EMBEDDING_VERSION,
                    extra["vector"],
                    source.hexdigest(),
                )

    def _finish(self, job: dict, state: str, error: str | None = None) -> bool:
        with self.db.connection() as conn:
            return jobs.finish(conn, job["job_id"], self.name, state, error)

    def _release(self, job: dict, delay: float = 0.0) -> bool:
        with self.db.connection() as conn:
            return jobs.release(conn, job["job_id"], self.name, delay)

    def _retry(self, job: dict, delay: float, error: str) -> bool:
        with self.db.connection() as conn:
            return jobs.retry_later(conn, job["job_id"], self.name, delay, error)

    # ----- the work -----

    async def do_steps(self, job: dict, ticket: dict, done: dict, info: dict) -> None:
        """The job's steps; `info` collects what the telemetry reports at the end."""
        s, b = ticket["subject"], ticket["body"]
        prompt = info["prompt"]
        telemetry.PROMPT_VERSION.set(prompt)
        if "triage" not in done:
            with telemetry.span("triage", attributes={"prompt.version": prompt}) as span:
                request = assistant.triage_request(b, prompt)
                answer, ms = await self.provider.acall("chat/completions", request)
                info["answer"], info["triage_ms"] = answer, ms
                try:
                    triage, run = read_triage(answer, ms, prompt)
                except ai.BadAnswer as error:
                    # The call cost tokens: keep its record, then the job fails (no retry).
                    run = run_record("triage", prompt, answer, ms, None, status="error")
                    info["runs"] = [run]
                    span.set_status(StatusCode.ERROR, str(error))
                    span.set_attribute("error.type", type(error).__name__)
                    await asyncio.to_thread(self._save_step, job, ticket, run, {})
                    raise error
                info["runs"], info["triage"] = [run], triage
                info["drafted_at"] = time.time()
                span.set_attributes(
                    {"app.team": triage.team, "app.needs_human": triage.needs_human}
                )
                await asyncio.to_thread(self._save_step, job, ticket, run, {"triage": triage})
        elif done["triage"]["status"] != "ok":
            raise assistant.NoAnswer(
                f"no valid answer (finish_reason {done['triage']['finish_reason']})"
            )
        if "embed" not in done:
            with telemetry.span("embed"):
                answer, ms, cached = await embed_cached(self.provider, self.cache, s, b)
                vector = ai.parse_embedding(answer)
                if cached:
                    answer = {**answer, "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
                output = f"vector {ai.EMBEDDING_VERSION}" + (" (from the cache)" if cached else "")
                run = run_record("embed", None, answer, ms, output)
                info.setdefault("runs", []).append(run)
                await asyncio.to_thread(self._save_step, job, ticket, run, {"vector": vector})
        if info.get("shadow") and "triage_shadow" not in done:
            await self.shadow_step(job, ticket, info["shadow"])

    async def shadow_step(self, job: dict, ticket: dict, shadow: str) -> None:
        """Module 5: the shadow release triages the same ticket. Its result is saved for
        comparison only (task triage_shadow); a failure here never fails the job."""
        prompt = self.rollout.release(shadow).prompt
        attrs = {
            "ticket.id": ticket["ticket_id"],
            "job.id": job["job_id"],
            "release.id": shadow,
            "prompt.version": prompt,
        }
        with telemetry.span(
            "triage (shadow)", attributes={"prompt.version": prompt, "app.release.id": shadow}
        ):
            telemetry.PROMPT_VERSION.set(prompt)
            try:
                answer, ms = await self.provider.acall(
                    "chat/completions", assistant.triage_request(ticket["body"], prompt)
                )
            except (ProviderError, BreakerOpen) as error:
                telemetry.event(
                    "ticket.shadowed",
                    attrs | {"outcome": "provider_error", "error.type": type(error).__name__},
                )
                return
            usage = answer.get("usage") or {}
            try:
                t = assistant.parse_triage(answer)
                outcome = "ok"
                attrs |= {"team": t.team, "needs_human": t.needs_human}
            except ai.BadAnswer as error:
                outcome = "no_answer" if isinstance(error, assistant.NoAnswer) else "bad_answer"
                t = None
            run = run_record(
                "triage_shadow",
                prompt,
                answer,
                ms,
                None if t is None else json.dumps({"team": t.team, "needs_human": t.needs_human}),
                status="ok" if t else "error",
            )
            run["release_id"] = shadow
            await asyncio.to_thread(self._save_step, job, ticket, run, {})
            telemetry.event(
                "ticket.shadowed",
                attrs
                | {
                    "outcome": outcome,
                    "triage_ms": round(ms, 1),
                    "cost_usd": run["cost_usd"],
                    "gen_ai.usage.input_tokens": usage.get("prompt_tokens"),
                    "gen_ai.usage.output_tokens": usage.get("completion_tokens"),
                    "gen_ai.response.finish_reasons": assistant.finish_reason(answer),
                },
            )

    async def _choose_release(self, ticket_id: str) -> dict:
        """The release (and its prompt) for this ticket: from release_state when a rollout is
        set up (Module 5), else RELEASE_ID / ASSISTANT_PROMPT."""
        try:
            state, changed = await asyncio.to_thread(self.rollout.current)
        except psycopg.errors.UndefinedTable:  # a database without migration 020
            state, changed = None, False
        if changed and state is not None:
            telemetry.event(
                "release.changed",
                {
                    "release.active": state.active,
                    "release.canary": state.canary,
                    "release.canary_share": state.canary_share,
                    "release.shadow": state.shadow,
                },
                severity="WARN",
            )
            logger.info("release state: %s", state)
            for rid in {state.active, state.canary, state.shadow} - {None}:
                telemetry.zero_series(self.rollout.release(rid).prompt, rid)
        if state is None:
            return {"release": self.settings.release_id, "prompt": self.settings.assistant_prompt}
        chosen = rollout.choose(state, ticket_id)
        info = {
            "release": chosen,
            "prompt": self.rollout.release(chosen).prompt,
            "canary": chosen == state.canary and chosen != state.active,
        }
        if state.shadow and state.shadow != chosen:
            info["shadow"] = state.shadow
        return info

    async def process(self, job: dict) -> str:
        """Run one job; return the state it ends in (or 'lost' if another worker took it).
        One span for the job, in the trace of the request that created the ticket."""
        info: dict = await self._choose_release(job["ticket_id"])
        releases.CURRENT.set(info["release"])  # this task's own context
        telemetry.REQUEST_ID.set(job.get("request_id"))
        attributes = {
            "app.job.id": job["job_id"],
            "app.ticket.id": job["ticket_id"],
            "app.job.attempt": job["attempts"],
            "app.release.id": info["release"] or "none",
            "prompt.version": info["prompt"],
        }
        with telemetry.tracer.start_as_current_span(
            "process ticket job",
            context=telemetry.context_from(job.get("trace_context")),
            kind=SpanKind.CONSUMER,
            attributes=attributes,
        ) as span:
            state, error = await self._process(job, info)
            self._report(job, state, error, info, span)
        return state

    async def _process(self, job: dict, info: dict) -> tuple[str, Exception | None]:
        error: Exception | None = None
        try:
            ticket, done = await asyncio.to_thread(self._load, job)
            if ticket is None:
                state = "failed"
                await asyncio.to_thread(self._finish, job, state, "the ticket does not exist")
                return state, None
            await self.do_steps(job, ticket, done, info)
            ok = await asyncio.to_thread(self._finish, job, "succeeded")
            self.rate_limited = 0
            state = "succeeded" if ok else "lost"
        except asyncio.CancelledError:
            # The worker is stopping and the job did not finish in time: give it back.
            await asyncio.to_thread(self._release, job)
            self.counts["released"] += 1
            logger.info("job %s: given back to the queue (the worker is stopping)", job["job_id"])
            raise
        except BreakerOpen as e:
            state, error = "released", e
            await asyncio.to_thread(self._release, job, e.retry_after)
        except (ai.BadAnswer, ProviderRejected) as e:
            state, error = "failed", e
            await asyncio.to_thread(self._finish, job, state, f"{type(e).__name__}: {e}")
        except ProviderRateLimited as e:
            # Over the quota is not the job's fault: the job waits and keeps its attempts.
            # (Measured by the course: when these waits counted as attempts, a burst turned
            # 99 of 180 jobs into dead letters, because the quota counts over a whole minute.)
            state, error = "waiting", e
            self.rate_limited += 1
            delay = max(
                e.retry_after or 0,
                jobs.backoff_seconds(
                    min(self.rate_limited, 6),
                    self.settings.retry_base_seconds,
                    self.settings.retry_cap_seconds,
                ),
            )
            await asyncio.to_thread(self._release, job, delay)
        except ProviderError as e:
            error = e
            message = f"{type(e).__name__}: {e}"
            if job["attempts"] >= job["max_attempts"]:
                state = "dead_letter"
                await asyncio.to_thread(self._finish, job, state, message)
            else:
                state = "retried"
                delay = jobs.backoff_seconds(
                    job["attempts"],
                    self.settings.retry_base_seconds,
                    self.settings.retry_cap_seconds,
                )
                await asyncio.to_thread(self._retry, job, delay, message)
        if state in self.counts:
            self.counts[state] += 1
        logger.info("job %s: %s (attempt %s)", job["job_id"], state, job["attempts"])
        return state, error

    def _report(self, job: dict, state: str, error: Exception | None, info: dict, span) -> None:
        """The job's telemetry: a ticket.triaged event when the job ended (succeeded, failed,
        dead letter), else a job.retry event; the metrics; the span's outcome."""
        release = info.get("release") or "none"
        prompt = info.get("prompt", self.settings.assistant_prompt)
        common = {
            "ticket.id": job["ticket_id"],
            "job.id": job["job_id"],
            "job.attempt": job["attempts"],
            "release.id": release,
            "prompt.version": prompt,
        }
        if error is not None:
            span.set_attribute("error.type", type(error).__name__)
        breaker = getattr(self.provider, "breaker", None)
        if breaker is not None and breaker.state != self._breaker_seen:
            self._breaker_seen = breaker.state
            telemetry.event(
                "breaker.changed",
                {"breaker.state": breaker.state},
                severity="WARN" if breaker.state == "open" else "INFO",
            )
        if state not in ("succeeded", "failed", "dead_letter"):
            span.set_attribute("app.outcome", state)
            telemetry.event(
                "job.retry",
                common
                | {"job.state": state, "error.type": type(error).__name__ if error else None},
                severity="WARN",
            )
            return
        outcome = {"succeeded": "ok", "dead_letter": "dead_letter"}.get(state)
        if outcome is None:
            outcome = {
                "NoAnswer": "no_answer",
                "BadAnswer": "bad_answer",
                "ProviderRejected": "rejected",
            }.get(type(error).__name__, "failed")
        runs = info.get("runs", [])
        cost = sum(r.get("cost_usd") or 0.0 for r in runs)
        answer = info.get("answer") or {}
        usage = answer.get("usage") or {}
        choices = answer.get("choices") or [{}]
        waited = info.get("drafted_at", time.time()) - job["created_at"].timestamp()
        attrs = common | {
            "outcome": outcome,
            "time_to_draft_s": round(waited, 3),
            "cost_usd": round(cost, 8),
            "triage_ms": round(info["triage_ms"], 1) if "triage_ms" in info else None,
            "gen_ai.response.model": answer.get("model"),
            "gen_ai.response.finish_reasons": choices[0].get("finish_reason"),
            "gen_ai.usage.input_tokens": usage.get("prompt_tokens"),
            "gen_ai.usage.output_tokens": usage.get("completion_tokens"),
            "gen_ai.usage.reasoning_output_tokens": (
                usage.get("completion_tokens_details") or {}
            ).get("reasoning_tokens"),
            "evidence": (answer.get("simulator") or {}).get(
                "evidence", "provider" if answer else None
            ),
            "error.type": type(error).__name__ if error else None,
            "release.canary": info.get("canary", False),
        }
        t = info.get("triage")
        if t is not None:
            attrs |= {"team": t.team, "needs_human": t.needs_human, "language": t.language}
        if telemetry.capture_content() and t is not None:
            attrs["answer.text"] = t.reply
        span.set_attribute("app.outcome", outcome)
        if outcome != "ok":
            span.set_status(StatusCode.ERROR, f"{outcome}: {error}")
        telemetry.event("ticket.triaged", attrs, severity="INFO" if outcome == "ok" else "ERROR")
        telemetry.zero_series(prompt, release)
        m = telemetry.instruments()
        decided = "none" if t is None else str(t.needs_human).lower()
        m.triaged.add(
            1,
            {
                "outcome": outcome,
                "prompt.version": prompt,
                "release.id": release,
                "needs_human": decided,
            },
        )
        if outcome == "ok":
            m.time_to_draft.record(waited, {"release.id": release})
        for r in runs:
            m.cost.add(
                r.get("cost_usd") or 0.0,
                {"task": r["task"], "prompt.version": prompt, "release.id": release},
            )

    async def run_once(self) -> int:
        """Claim what fits into the free slots and start it. Returns the number of new jobs."""
        free = self.concurrency - len(self.in_flight)
        if free <= 0:
            return 0
        claimed = await asyncio.to_thread(self._claim, free)
        for job in claimed:
            task = asyncio.create_task(self.process(job))
            self.in_flight.add(task)
            task.add_done_callback(self.in_flight.discard)
        self.counts["claimed"] += len(claimed)
        return len(claimed)

    async def drain(self) -> None:
        """Run until no job is ready and none is in flight (for --once and the tests)."""
        while True:
            started = await self.run_once()
            if not self.in_flight and not started:
                return
            if self.in_flight:
                await asyncio.wait(self.in_flight, return_when=asyncio.FIRST_COMPLETED)

    async def run_forever(self, stop: asyncio.Event) -> None:
        stopping = asyncio.create_task(stop.wait())
        while not stop.is_set():
            started = await self.run_once()
            if started == 0 or len(self.in_flight) >= self.concurrency:
                await asyncio.wait(
                    {stopping} | self.in_flight,
                    timeout=self.settings.worker_poll_seconds,
                    return_when=asyncio.FIRST_COMPLETED,
                )
        await self.shutdown()

    async def shutdown(self) -> None:
        """Graceful shutdown: no new jobs; the running ones get WORKER_DRAIN_SECONDS to
        finish; the rest go back to the queue."""
        if not self.in_flight:
            return
        seconds = self.settings.worker_drain_seconds
        logger.info(
            "stopping: %d job(s) running, waiting up to %.0f s", len(self.in_flight), seconds
        )
        _, pending = await asyncio.wait(set(self.in_flight), timeout=seconds)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


def make_worker(settings: Settings, name: str | None = None, provider: Provider | None = None):
    db = Database(
        settings.database_url,
        min_size=1,
        max_size=max(2, settings.worker_concurrency + 1),
        timeout=settings.db_pool_timeout,
    )
    # No quick retries in the worker: a failed job goes back to the queue and waits there.
    provider = provider or make_provider(settings, retries=0)
    cache = make_cache(settings.cache_url, settings.cache_timeout)
    worker = Worker(db, provider, settings, cache, name)
    if telemetry.start(settings, "ticket-worker"):  # Module 3 of the MLOps course
        watch_queue(worker)
        telemetry.zero_series(settings.assistant_prompt, settings.release_id or "none")
    return worker


def watch_queue(worker: Worker) -> None:
    """Gauges read when the metrics are exported: the queue (from the jobs table) and the
    circuit breaker. They are the signals of a provider outage (Module 6)."""
    from opentelemetry.metrics import Observation

    cached = {"at": 0.0, "stats": None}

    def stats() -> dict | None:
        if time.monotonic() - cached["at"] > 1.0:
            try:
                with telemetry.quiet(), worker.db.connection() as conn:
                    cached["stats"] = jobs.stats(conn)
            except Exception:  # the database is down: no number, rather than a wrong one
                cached["stats"] = None
            cached["at"] = time.monotonic()
        return cached["stats"]

    def depth(_options):
        st = stats()
        if st is not None:
            yield Observation(st["queued"], {"state": "queued"})
            yield Observation(st["running"], {"state": "running"})
            yield Observation(st["dead_letter"], {"state": "dead_letter"})

    def oldest(_options):
        st = stats()
        if st is not None:
            yield Observation(st["oldest_queued_seconds"])

    def breaker(_options):
        b = getattr(worker.provider, "breaker", None)
        yield Observation(1 if b is not None and b.state == "open" else 0)

    m = telemetry.meter()
    m.create_observable_gauge("app.queue.depth", [depth], "{job}", "Jobs in the queue, by state")
    m.create_observable_gauge("app.queue.oldest_age", [oldest], "s", "Age of the oldest queued job")
    m.create_observable_gauge(
        "app.provider.breaker_open", [breaker], "1", "1 = the circuit is open"
    )


async def main_async(args: argparse.Namespace) -> int:
    settings = load_settings()
    if args.concurrency:
        from dataclasses import replace

        settings = replace(settings, worker_concurrency=args.concurrency)
    worker = make_worker(settings, args.name)
    worker.db.open()
    started = time.perf_counter()
    noun = "job" if worker.concurrency == 1 else "jobs"
    print(
        f"Worker {worker.name}: up to {worker.concurrency} {noun} at a time. "
        + ("Takes what is queued, then stops." if args.once else "Stop it with Ctrl+C.")
    )
    stop = asyncio.Event()

    def on_signal(*_) -> None:
        if not stop.is_set():
            print(
                f"Stopping: no new jobs; {len(worker.in_flight)} running job(s) get up to "
                f"{settings.worker_drain_seconds:.0f} s to finish.",
                flush=True,
            )
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, on_signal)
        except (NotImplementedError, AttributeError, ValueError):  # Windows
            signal.signal(sig, lambda *a: loop.call_soon_threadsafe(on_signal))
    try:
        if args.once:
            await worker.drain()
        else:
            await worker.run_forever(stop)
    finally:
        telemetry.shutdown()  # send what waits in the batches before the process ends
        worker.db.close()
        await worker.provider.aclose()
        worker.provider.close()
        if worker.cache is not None:
            await worker.cache.close()
    c = worker.counts
    print(
        f"Done in {time.perf_counter() - started:.1f} s: {c['claimed']} taken, {c['succeeded']} "
        f"succeeded, {c['waiting']} waiting for the quota, {c['retried']} to retry later, "
        f"{c['failed']} failed, "
        f"{c['dead_letter']} dead letters, {c['released']} given back to the queue."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the worker that does the AI work of jobs.")
    parser.add_argument("--once", action="store_true", help="take what is queued, then stop")
    parser.add_argument(
        "--concurrency", type=int, help="jobs at the same time (WORKER_CONCURRENCY)"
    )
    parser.add_argument("--name", help="the worker's name in the jobs table")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s [%(request_id)s]: %(message)s",
    )
    for handler in logging.getLogger().handlers:  # every log line gets the request ID
        handler.addFilter(telemetry.RequestIdFilter())
    try:
        return asyncio.run(main_async(args))
    except SettingsError as error:
        print(f"Settings error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
