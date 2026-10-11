"""Run a practice scenario on your own running service (the MLOps course, Modules 4 to 6).

    python -m scripts.scenario canary --v2 1.5.0-3f9a1c --v3 1.5.0-8b20d4
    python -m scripts.scenario outage --v2 1.5.0-3f9a1c

Scenarios (each one is a practice situation that we cause on purpose; none is a real event):
- normal-week   a week of Larkfield's tickets (5,754), sent 2 a second, with reviews and questions
- release-full  prompt v3 replaces v2 for every ticket, and nobody rolls back (what happened)
- canary        prompt v3 for 10% of the tickets; the alert fires; the release is rolled back
- shadow        prompt v3 runs beside v2 on every ticket, and no customer sees its answers
- outage        the AI provider fails for 5 minutes (the simulator's outage mode), then recovers
- stale-index   a document changes and the index is not rebuilt; later, the provider's model
                version changes for a while
- drift         more French tickets, then more questions that the policy does not answer

Start first: the simulated provider (python -m simulator), the API (fastapi run, with
RATE_LIMIT_PER_MINUTE=0), two workers (python -m ticket_api.worker), with telemetry on
(TELEMETRY_FILE and, for the alerts, the Grafana stack). The scenario writes its own actions
to practice/actions.jsonl in the telemetry format (event practice.action), so that python -m
ops can show them on the same timeline. Time runs faster than in real life: 2 tickets a second
is about 140 times Larkfield's average (822 a day).
"""

import argparse
import asyncio
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import httpx

from scripts import practice
from scripts.send_reviews import labels
from ticket_api.config import load_env

ACTIONS = Path("practice/actions.jsonl")
QUESTIONS = [
    "Where is my parcel and how do I track it?",
    "How do I return a damaged item?",
    "When will I get my refund?",
    "How much is delivery and when is it free?",
    "Can I change or cancel my order?",
    "How does the warranty work?",
    "Do you deliver large items like sheds?",
    "What are your opening hours?",
]
REVIEW_TEAMS = ("delivery", "returns", "payment", "warranty", "account")


class Run:
    def __init__(self, args):
        self.args = args
        self.rng = random.Random(args.seed)
        self.t0 = time.time()
        headers = {"X-API-Key": os.environ["API_KEY"]} if os.environ.get("API_KEY") else {}
        self.api = httpx.AsyncClient(
            base_url=args.url, headers=headers, timeout=60, limits=httpx.Limits(max_connections=200)
        )
        self.sim = httpx.AsyncClient(base_url=args.simulator, timeout=10)
        self.grafana = (
            httpx.AsyncClient(base_url=args.grafana, auth=("admin", "admin"), timeout=10)
            if args.grafana
            else None
        )
        self.sent: list[dict] = []  # {ticket_id, case_id, time}
        self.truth = labels()
        self.stop = asyncio.Event()
        self.tasks: list[asyncio.Task] = []
        ACTIONS.parent.mkdir(exist_ok=True)

    def action(self, name: str, **detail) -> None:
        now = time.time()
        rec = {
            "signal": "log",
            "time": now,
            "service": "practice",
            "event": "practice.action",
            "body": name,
            "attributes": {"action": name, **detail},
        }
        with ACTIONS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"+{(now - self.t0) / 60:5.1f} min  {name} {detail if detail else ''}", flush=True)

    def ops(self, *argv: str) -> None:
        out = subprocess.run([sys.executable, "-m", "ops", *argv], capture_output=True, text=True)
        self.action("ops " + " ".join(argv), output=(out.stdout or out.stderr).strip()[-300:])

    # ----- traffic -----

    async def wait(self, seconds: float) -> None:
        await asyncio.sleep(seconds * self.args.scale)

    async def tickets(self, n: int, rate: float, weights: dict | None = None) -> None:
        n = max(1, round(n * self.args.scale))
        pool = practice.load_tickets()
        chosen = practice.choose(pool, n, self.rng, weights)
        start = time.perf_counter()
        pending = []
        for i, ticket in enumerate(chosen):
            delay = start + i / rate - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)
            pending.append(asyncio.create_task(self._send(ticket)))
        await asyncio.gather(*pending)

    async def _send(self, ticket: dict) -> None:
        body = practice.body_of(ticket, self.rng.choice(practice.CUSTOMERS))
        try:
            r = await self.api.post("/v1/tickets", json=body)
        except httpx.HTTPError:
            return
        if r.status_code < 300:
            self.sent.append(
                {
                    "ticket_id": r.json()["ticket_id"],
                    "case_id": ticket["case_id"],
                    "time": time.time(),
                }
            )

    async def questions(self, rate: float) -> None:
        while not self.stop.is_set():
            q = self.rng.choice(QUESTIONS)
            who = (
                {"X-Customer-ID": self.rng.choice(practice.CUSTOMERS)}
                if self.rng.random() < 0.9
                else {}
            )
            try:
                await self.api.post("/v1/answers", json={"question": q}, headers=who)
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1 / rate)

    async def reviews(self, share: float, delay: float) -> None:
        """Agents review a share of the tickets, `delay` seconds after they arrived."""
        done = 0
        while not self.stop.is_set() or done < len(self.sent):
            now = time.time()
            while done < len(self.sent) and self.sent[done]["time"] + delay <= now:
                s = self.sent[done]
                done += 1
                label = self.truth[s["case_id"]]
                if self.rng.random() >= share or label["expected_team"] not in REVIEW_TEAMS:
                    continue
                try:
                    await self.api.post(
                        f"/v1/tickets/{s['ticket_id']}/review",
                        json={
                            "team": label["expected_team"],
                            "needs_human": label["expected_needs_human"],
                            "reviewed_by": f"agent-{self.rng.randrange(1, 13):02d}",
                        },
                    )
                except httpx.HTTPError:
                    pass
            if (
                self.stop.is_set()
                and done < len(self.sent)
                and self.sent[done]["time"] + delay > now
            ):
                break  # the scenario is over; later reviews would arrive after it
            await asyncio.sleep(1)

    def background(self, coro) -> None:
        self.tasks.append(asyncio.create_task(coro))

    async def finish(self) -> None:
        self.stop.set()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        await self.api.aclose()
        await self.sim.aclose()
        if self.grafana:
            await self.grafana.aclose()

    # ----- the provider and the alerts -----

    async def sim_mode(self, mode: str) -> None:
        await self.sim.post("/admin/mode", json={"mode": mode})
        self.action("simulator mode", mode=mode)

    async def sim_model_version(self, version: str) -> None:
        await self.sim.post("/admin/model-version", json={"model_version": version})
        self.action("simulator model version", model_version=version)

    async def firing(self) -> set[str]:
        """The UIDs of the alert rules that fire now (Grafana's own evaluation)."""
        if not self.grafana:
            return set()
        try:
            if not getattr(self, "uids", None):
                rules = (await self.grafana.get("/api/v1/provisioning/alert-rules")).json()
                self.uids = {rule["title"]: rule["uid"] for rule in rules}
            r = await self.grafana.get("/api/prometheus/grafana/api/v1/alerts")
            alerts = r.json()["data"]["alerts"]
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            return set()
        firing = [a for a in alerts if a.get("state") in ("Alerting", "firing")]
        return {
            self.uids.get(a["labels"].get("alertname"), a["labels"].get("alertname"))
            for a in firing
        }

    async def watch_alerts(self) -> None:
        """Logs every alert that starts or stops firing (Grafana's own evaluation)."""
        seen: set[str] = set()
        while not self.stop.is_set():
            now = await self.firing()
            for uid in sorted(now - seen):
                self.action("alert firing", alert=uid)
            for uid in sorted(seen - now):
                self.action("alert resolved", alert=uid)
            seen = now
            await asyncio.sleep(5)

    async def wait_alert(self, uid: str, timeout: float) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if uid in await self.firing():
                return True
            await asyncio.sleep(5)
        return False


async def run_scenario(name: str, args) -> None:
    r = Run(args)
    r.action("scenario start", scenario=name)
    if r.grafana:
        r.background(r.watch_alerts())
    if name != "outage":
        await r.sim_mode("normal")
    if name in (
        "normal-week",
        "release-full",
        "canary",
        "shadow",
        "outage",
        "drift",
        "stale-index",
    ):
        r.ops("rollout", "start", args.v2, "--reason", f"practice scenario {name}")
    if name == "normal-week":
        r.background(r.reviews(0.3, 300))
        r.background(r.questions(0.2))
        await r.tickets(5754, 2.0)
    elif name == "release-full":
        r.background(r.reviews(0.5, 120))
        sending = asyncio.create_task(r.tickets(2400, 2.0))
        await r.wait(300)
        r.ops("rollout", "start", args.v3, "--reason", "the cheaper prompt, for every ticket")
        await sending
    elif name == "canary":
        r.background(r.reviews(0.5, 120))
        sending = asyncio.create_task(r.tickets(2400, 2.0))
        await r.wait(300)
        r.ops("rollout", "canary", args.v3, "--share", "0.1", "--reason", "canary of prompt v3")
        fired = await r.wait_alert("no-answer", 900)
        r.action("on-call reads the alert" if fired else "no alert in 15 minutes")
        await r.wait(60)  # an assumption: one minute for a person to act
        r.ops(
            "rollout", "rollback", "--reason", "alert no-answer: canary tickets without an answer"
        )
        await sending
    elif name == "shadow":
        r.ops("rollout", "shadow", args.v3, "--reason", "shadow run of prompt v3")
        await r.tickets(600, 2.0)
        r.ops("rollout", "stop", "--reason", "shadow run finished")
    elif name == "outage":
        await r.sim_mode("normal")
        sending = asyncio.create_task(r.tickets(1200, 1.0))
        await r.wait(300)
        await r.sim_mode("outage")
        await r.wait(300)
        await r.sim_mode("normal")
        await sending
        await r.wait(120)  # the queue drains
    elif name == "stale-index":
        r.background(r.questions(1.0))
        sending = asyncio.create_task(r.tickets(450, 0.5))
        await r.wait(240)
        out = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.update_document",
                "delivery-policy",
                "--replace",
                "free at 100",
                "free at 75",
            ],
            capture_output=True,
            text=True,
        )
        r.action("document changed, index not rebuilt", output=out.stdout.strip()[-200:])
        fired = await r.wait_alert("old-sources", 300)
        r.action("on-call reads the alert" if fired else "no alert in 5 minutes")
        await r.wait(60)
        out = subprocess.run(
            [sys.executable, "-m", "scripts.reindex"], capture_output=True, text=True
        )
        r.action("index rebuilt", output=out.stdout.strip()[-200:])
        await r.wait(120)
        await r.sim_model_version("gpt-6-luna-2026-11-04")
        fired = await r.wait_alert("model-version-changed", 300)
        r.action("on-call reads the alert" if fired else "no alert in 5 minutes")
        await r.wait(120)
        await r.sim_model_version("gpt-6-luna-2026-09-22")
        await sending
    elif name == "drift":
        r.background(r.reviews(0.5, 120))
        await r.tickets(1000, 2.0)
        r.action("more French tickets from now (a new region)")
        await r.tickets(1000, 2.0, {"lang:fr": 6.0})
        r.action("more questions that the policy does not answer (a new payment option)")
        await r.tickets(1000, 2.0, {"unanswerable": 6.0})
        await r.wait(150)  # the last reviews
    r.action("scenario end", scenario=name, tickets=len(r.sent))
    await r.finish()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "scenario",
        choices=[
            "normal-week",
            "release-full",
            "canary",
            "shadow",
            "outage",
            "stale-index",
            "drift",
        ],
    )
    parser.add_argument("--v2", required=True, help="the release ID of prompt v2 (the live one)")
    parser.add_argument("--v3", help="the release ID of prompt v3 (the candidate)")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--simulator", default="http://127.0.0.1:8300")
    parser.add_argument("--grafana", default="", help="for example http://127.0.0.1:3000")
    parser.add_argument("--seed", type=int, default=25)
    parser.add_argument("--scale", type=float, default=1.0, help="shorter runs: 0.1 = a tenth")
    args = parser.parse_args(argv)
    if args.scenario in ("release-full", "canary", "shadow") and not args.v3:
        parser.error(f"{args.scenario} needs --v3")
    load_env()
    asyncio.run(run_scenario(args.scenario, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
