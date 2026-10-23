"""The provider simulator: OpenAI-compatible endpoints that answer with real recorded answers.

    POST /{provider}/v1/chat/completions      POST /{provider}/v1/embeddings      GET /{provider}/v1/models

Providers: azure, azure-canada (a simulated second region with the same recordings), local (gemma3:4b),
fernway (made up). For every request the simulator:

1. writes a line to its egress log (which machine, which provider, which key: a simulated network log);
2. refuses it if the simulated egress rule allows only the gateway (SIM_EGRESS=gateway-only);
3. checks the key (each provider's practice keys, provsim/accounts.py);
4. applies the practice controls (outage, slow answers, errors, rate limits: always "simulated");
5. applies the recorded feature rules (provsim/features.py): a request that the real deployment refused is
   refused with the recorded error;
6. looks up the recorded answer for exactly this request (provsim/store.py). None: HTTP 422 no_recording.
   It never invents an answer;
7. waits the recorded latency times SIM_SPEED (0 = no waiting), answers, and adds the call to the bill.

Headers on every answer say where it comes from: x-sim-source (course and file), x-sim-recorded-latency-ms,
x-sim-match, and x-sim-constructed for the one constructed answer.
"""

import asyncio
import json
import os
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

from provsim import accounts, features
from provsim.store import Store, request_key

PROJECT = Path(__file__).resolve().parent.parent
STATE = Path(os.environ.get("ESTATE_STATE", PROJECT / "state"))   # practice state; git-ignored
COURSES = {"agents": "agents course", "evaluation": "evaluation course", "capstone": "capstone course",
           "llm-apps": "LLM applications course", "governance": "this course", "constructed": "constructed"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Simulator:
    """The state of one running simulator: controls, counters, the bill and the egress log."""

    def __init__(self, state_dir: Path, speed: float = 0.0, egress: str = "open", replay_clock: bool = False,
                 store: Store | None = None, seed: int = 32):
        self.store = store or Store()
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.speed = speed
        self.egress = egress
        self.replay_clock = replay_clock
        self.controls: list[dict] = []
        self.rng = random.Random(seed)
        self.lock = threading.Lock()
        self.stats = {"requests": 0, "answered": 0, "no_recording": 0, "feature_refused": 0, "simulated_failures": 0,
                      "egress_blocked": 0, "bad_key": 0}
        self.usage_path = self.state_dir / "provider-usage.jsonl"
        self.egress_path = self.state_dir / "egress.csv"
        if not self.egress_path.exists():
            self.egress_path.write_text("time,source_host,destination,provider,key_id,status,bytes_out\n")

    # --- logs ---------------------------------------------------------------------------------------
    def when(self, request: Request) -> str:
        t = request.headers.get("x-replay-time")
        return t if (self.replay_clock and t) else _now_iso()

    def log_egress(self, when: str, request: Request, provider: str, key_id: str, status: int, size: int) -> None:
        host = request.headers.get("x-sim-host", "unknown")
        dest = accounts.PROVIDERS.get(provider, {}).get("host", provider)
        with self.lock, self.egress_path.open("a", encoding="utf-8") as f:
            f.write(f"{when},{host},{dest},{provider},{key_id},{status},{size}\n")

    def bill(self, when: str, provider: str, key_id: str, deployment: str, usage: dict) -> None:
        tin = int(usage.get("prompt_tokens") or 0)
        tout = int(usage.get("completion_tokens") or 0)
        row = {"time": when, "provider": provider, "key_id": key_id, "deployment": deployment, "tokens_in": tin,
               "tokens_out": tout, "cost_usd": round(accounts.cost_usd(deployment, tin, tout), 8)}
        with self.lock, self.usage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    # --- practice controls --------------------------------------------------------------------------
    def control_for(self, provider: str, deployment: str) -> dict | None:
        for c in self.controls:
            if c["provider"] in (provider, "*") and c.get("deployment") in (None, "", deployment):
                if c.get("requests_left") is not None:
                    if c["requests_left"] <= 0:
                        continue
                    c["requests_left"] -= 1
                return c
        return None


def error(status: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message, "type": "simulated"}}, status, headers=headers)


def key_of(request: Request) -> str:
    if request.headers.get("api-key"):
        return request.headers["api-key"]
    auth = request.headers.get("authorization", "")
    return auth[7:].strip() if auth.lower().startswith("bearer ") else ""


async def model_call(request: Request) -> JSONResponse:
    sim: Simulator = request.app.state.sim
    provider = request.path_params["provider"]
    endpoint = "embeddings" if request.url.path.endswith("/embeddings") else "chat"
    when = sim.when(request)
    sim.stats["requests"] += 1
    raw = await request.body()
    p = accounts.PROVIDERS.get(provider)
    if p is None:
        return error(404, "unknown_provider", f"There is no simulated provider {provider!r}.")
    key = key_of(request)
    known = accounts.KEYS.get(key)
    key_id = known[0] if known else ("none" if not key else "unknown")
    # 1-2. The simulated network: the egress log, and the egress rule.
    if sim.egress == "gateway-only" and provider != "local" and not (known and known[3] == "gateway"):
        sim.stats["egress_blocked"] += 1
        sim.log_egress(when, request, provider, key_id, 403, len(raw))
        return error(403, "egress_blocked", f"Blocked by Larkfield's egress rule (simulated network): only the model "
                     f"gateway may connect to {p['host']}.", {"x-sim-egress": "blocked"})
    # 3. The key.
    if not p.get("no_key") and not (known and provider in known[1]):
        sim.stats["bad_key"] += 1
        sim.log_egress(when, request, provider, key_id, 401, len(raw))
        return error(401, "invalid_key", "Invalid API key for this provider (simulated provider).")
    try:
        body = json.loads(raw or b"{}")
    except json.JSONDecodeError:
        sim.log_egress(when, request, provider, key_id, 400, len(raw))
        return error(400, "invalid_json", "The request body is not valid JSON.")
    if body.get("stream"):
        sim.log_egress(when, request, provider, key_id, 400, len(raw))
        return error(400, "stream_not_simulated", "Streaming is not simulated: send the request without stream.")
    deployment = str(body.get("model", ""))
    d = features.DEPLOYMENTS.get(deployment)
    if deployment not in p["deployments"] or d is None or d.endpoint != endpoint:
        sim.log_egress(when, request, provider, key_id, 404, len(raw))
        return error(404, "DeploymentNotFound", f"The deployment {deployment!r} does not exist at {provider} for "
                     f"{endpoint} (simulated provider). Deployments: {', '.join(p['deployments'])}.")
    headers = {"x-sim-provider": provider, "x-sim-deployment": deployment}
    # 4. Practice controls (simulated failures).
    control = sim.control_for(provider, deployment)
    extra_wait = 0.0
    if control:
        mode = control["mode"]
        headers["x-sim-control"] = mode
        if mode == "down":
            sim.stats["simulated_failures"] += 1
            sim.log_egress(when, request, provider, key_id, 503, len(raw))
            return error(503, "simulated_outage", f"{provider} is unavailable (a simulated outage).", headers)
        if mode == "errors" and sim.rng.random() < float(control.get("rate", 0.5)):
            sim.stats["simulated_failures"] += 1
            sim.log_egress(when, request, provider, key_id, 500, len(raw))
            return error(500, "simulated_server_error", "The provider had an internal error (simulated).", headers)
        if mode == "rate_limit":
            sim.stats["simulated_failures"] += 1
            sim.log_egress(when, request, provider, key_id, 429, len(raw))
            # The hints that the real provider sent in the scaling course's recordings: both, different.
            return error(429, "simulated_rate_limit", "Too many requests (simulated rate limit).",
                         {**headers, "retry-after": "30", "retry-after-ms": str(control.get("retry_after_ms", 1256))})
        if mode == "slow":
            extra_wait = float(control.get("seconds", 5.0))
    # 5. Recorded feature rules.
    refused = features.check(deployment, body)
    if refused:
        rule_id, status, err_body, source = refused
        sim.stats["feature_refused"] += 1
        sim.log_egress(when, request, provider, key_id, status, len(raw))
        return JSONResponse(err_body, status, headers={**headers, "x-sim-rule": rule_id, "x-sim-source": source})
    # 6. The recorded answer.
    repeat = request.headers.get("x-sim-repeat")
    answer = sim.store.pick(body, int(repeat) if repeat and repeat.isdigit() else None)
    if answer is None:
        sim.stats["no_recording"] += 1
        sim.log_egress(when, request, provider, key_id, 422, len(raw))
        return error(422, "no_recording", f"The provider simulator has no recording of this request (key "
                     f"{request_key(body)}). It answers only requests that a course recorded, byte for byte; it "
                     "never invents an answer.", headers)
    headers.update({
        "x-sim-source": f"{COURSES.get(answer.course, answer.course)}: {answer.file}",
        "x-sim-recorded-latency-ms": str(round(answer.latency_s * 1000)),
    })
    if answer.constructed:
        headers["x-sim-constructed"] = "true"
    sent, recorded = body.get("reasoning_effort"), answer.reasoning_effort
    headers["x-sim-match"] = "exact" if sent == recorded else (
        f"content; recorded with reasoning_effort={recorded or 'not set'}, sent {sent or 'not set'}")
    # 7. Wait (recorded latency x speed), answer, bill.
    wait = answer.latency_s * sim.speed + extra_wait
    if wait > 0:
        await asyncio.sleep(wait)
    sim.log_egress(when, request, provider, key_id, answer.error["status"] if answer.error else 200, len(raw))
    if answer.error:
        return JSONResponse(answer.error["body"], answer.error["status"], headers=headers)
    sim.stats["answered"] += 1
    sim.bill(when, provider, key_id, deployment, answer.response.get("usage") or {})
    return JSONResponse(answer.response, 200, headers=headers)


async def models(request: Request) -> JSONResponse:
    p = accounts.PROVIDERS.get(request.path_params["provider"])
    if p is None:
        return error(404, "unknown_provider", "There is no such simulated provider.")
    data = [{"id": n, "object": "model", "model_version": features.DEPLOYMENTS[n].model_version,
             "endpoint": features.DEPLOYMENTS[n].endpoint, "tools": features.DEPLOYMENTS[n].tools,
             "structured_output": features.DEPLOYMENTS[n].structured_output} for n in p["deployments"]]
    return JSONResponse({"object": "list", "data": data})


async def health(request: Request) -> JSONResponse:
    sim: Simulator = request.app.state.sim
    return JSONResponse({"ok": True, "recordings": len(sim.store), "speed": sim.speed, "egress": sim.egress})


async def admin_control(request: Request) -> JSONResponse:
    """Practice controls: {"provider": "azure", "deployment": "chat-small" (optional), "mode": "down" | "slow" |
    "errors" | "rate_limit" | "normal", "seconds": 5, "rate": 0.5, "requests": 20 (optional: only the next N)}."""
    sim: Simulator = request.app.state.sim
    c = await request.json()
    if c.get("mode") == "normal":
        sim.controls = [x for x in sim.controls if not (x["provider"] == c.get("provider", "*") and
                                                        x.get("deployment") in (None, "", c.get("deployment")))]
        if c.get("provider", "*") == "*":
            sim.controls = []
    else:
        if c.get("mode") not in ("down", "slow", "errors", "rate_limit"):
            return error(400, "bad_mode", "mode: down, slow, errors, rate_limit or normal")
        sim.controls.insert(0, {"provider": c.get("provider", "*"), "deployment": c.get("deployment"),
                                "mode": c["mode"], "seconds": c.get("seconds", 5.0), "rate": c.get("rate", 0.5),
                                "requests_left": c.get("requests")})
    return JSONResponse({"controls": sim.controls})


async def admin_settings(request: Request) -> JSONResponse:
    sim: Simulator = request.app.state.sim
    if request.method == "POST":
        s = await request.json()
        if "egress" in s:
            sim.egress = s["egress"]
        if "speed" in s:
            sim.speed = float(s["speed"])
    return JSONResponse({"egress": sim.egress, "speed": sim.speed, "controls": sim.controls, "stats": sim.stats})


async def admin_bill(request: Request) -> PlainTextResponse:
    """The provider's bill as CSV, one line per key and deployment: what a finance team receives."""
    sim: Simulator = request.app.state.sim
    month = request.query_params.get("month", "")
    provider = request.query_params.get("provider", "")
    totals: dict[tuple, list] = {}
    if sim.usage_path.exists():
        for line in sim.usage_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if (month and not r["time"].startswith(month)) or (provider and r["provider"] != provider):
                continue
            k = (r["time"][:7], r["provider"], r["key_id"], r["deployment"])
            t = totals.setdefault(k, [0, 0, 0, 0.0])
            t[0] += 1
            t[1] += r["tokens_in"]
            t[2] += r["tokens_out"]
            t[3] += r["cost_usd"]
    lines = ["month,provider,key_id,deployment,requests,tokens_in,tokens_out,cost_usd"]
    for (m, prov, kid, dep), (n, tin, tout, cost) in sorted(totals.items()):
        lines.append(f"{m},{prov},{kid},{dep},{n},{tin},{tout},{cost:.6f}")
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/csv")


async def admin_egress(request: Request) -> PlainTextResponse:
    sim: Simulator = request.app.state.sim
    return PlainTextResponse(sim.egress_path.read_text(encoding="utf-8"), media_type="text/csv")


async def admin_reset(request: Request) -> JSONResponse:
    """Forget controls, counters, the bill and the egress log (a fresh start for a practice run)."""
    sim: Simulator = request.app.state.sim
    sim.controls = []
    sim.stats = {k: 0 for k in sim.stats}
    sim.store._next.clear()
    for path in (sim.usage_path, sim.egress_path):
        if path.exists():
            path.unlink()
    sim.egress_path.write_text("time,source_host,destination,provider,key_id,status,bytes_out\n")
    return JSONResponse({"reset": True})


def create_app(state_dir: Path | None = None, speed: float | None = None, egress: str | None = None,
               replay_clock: bool | None = None, store: Store | None = None) -> Starlette:
    env = os.environ
    sim = Simulator(Path(state_dir or STATE / "provider"),
                    float(env.get("SIM_SPEED", "0")) if speed is None else speed,
                    env.get("SIM_EGRESS", "open") if egress is None else egress,
                    (env.get("SIM_REPLAY_CLOCK", "off") == "on") if replay_clock is None else replay_clock, store)
    app = Starlette(routes=[
        Route("/health", health),
        Route("/{provider}/v1/chat/completions", model_call, methods=["POST"]),
        Route("/{provider}/v1/embeddings", model_call, methods=["POST"]),
        Route("/{provider}/v1/models", models),
        Route("/admin/control", admin_control, methods=["POST"]),
        Route("/admin/settings", admin_settings, methods=["GET", "POST"]),
        Route("/admin/bill", admin_bill),
        Route("/admin/egress", admin_egress),
        Route("/admin/reset", admin_reset, methods=["POST"]),
    ])
    app.state.sim = sim
    app.state.started = time.time()
    return app
