"""The model gateway: one door for every model call of the estate. It speaks the OpenAI-compatible API,
so an app changes its base URL and its credential, and asks for a capability instead of a model.

    POST /v1/chat/completions    POST /v1/embeddings    GET /v1/models

Every request passes the same checks, in this order; the first one that fails answers, and the usage
store records which check it was:

    1 configuration   the replica has a snapshot (estate/configstore.py)          503 control_unavailable
    2 identity        a valid access token for the model gateway                  401 invalid_token, ...
    3 registration    the agent is registered and active                          403 not_registered, agent_suspended
    4 capability      it asks for a capability that its registration lists        400/403 capability_...
    5 data class      the request's data class is allowed (header X-Data-Class)   403 data_class_not_allowed
    6 kill switches   no switch stops this agent, capability or everything         403 stopped
    7 failure mode    if a control cannot run: fail open or closed by risk tier   503 control_unavailable
    8 limits          rate per minute, tokens per day, budget per month, steps   429 rate_limited, ...
    9 guardrails      card numbers redacted, secrets blocked                      400 blocked_by_guardrail
   10 route           the mapping's primary, then its fallbacks                    503 no_provider_available
   11 record          one row in the usage store, then the answer with headers that name the model that answered

The gateway runs as several replicas (python -m gateway --replica a|b|c) behind one address (gateway/front.py).
Each replica is stateless: what it must remember is in the usage store (shared) and the control plane.
"""

import asyncio
import contextlib
import json
import os
import time
import uuid
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from estate import catalog as catalog_mod
from estate import clock, identity, paths, switches
from estate.usage import StoreDown, UsageStore, windows
from gateway import guardrails, telemetry
from gateway.config import ConfigCache

RANK = {"low": 0, "medium": 1, "high": 2}
RETRYABLE = {429, 500, 502, 503, 504}


class Refused(Exception):
    def __init__(self, status: int, code: str, message: str, check: str, headers: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.check, self.headers = status, code, check, headers or {}


class Replica:
    """The state of one replica: its config cache, its upstream client, its local counters and breakers."""

    def __init__(self, name: str, cache: ConfigCache, store: UsageStore, secrets: dict, provsim_url: str,
                 transport: httpx.AsyncBaseTransport | None = None, timeout: float = 60.0):
        self.name = name
        self.cache = cache
        self.store = store
        self.secrets = secrets
        self.provsim_url = provsim_url.rstrip("/")
        self.client = httpx.AsyncClient(transport=transport, timeout=timeout)
        self.local: dict[tuple, dict] = {}         # counters kept here while the usage store is down
        self.pending: list[dict] = []              # usage rows to write when the store is back
        self.last_known: dict[tuple, dict] = {}    # the last counts read from the store
        self.breakers: dict[str, list] = {}        # provider -> [failures in a row, open until]
        self.faults = {"usage_store": "up"}
        self.verifier_kid = None
        self.verifier: identity.Verifier | None = None

    # --- helpers ---------------------------------------------------------------------------------------
    def verify(self, snap: dict, token: str) -> dict:
        jw = snap.get("jwks") or {"keys": []}
        kid = ",".join(k["kid"] for k in jw["keys"])
        if self.verifier is None or kid != self.verifier_kid:
            self.verifier, self.verifier_kid = identity.Verifier(jw), kid
        return self.verifier.verify(token, "model-gateway", now=clock.now().timestamp())

    def counter(self, subject: str, window: str, degraded: bool) -> dict:
        """The shared count (usage store), plus what this replica served while the store was down. Degraded:
        the last count this replica read, plus its own since then; the other replicas' spending is not seen."""
        local = self.local.get((subject, window), {"cost_usd": 0.0, "tokens": 0, "calls": 0})
        if degraded:
            known = self.last_known.get((subject, window), {"cost_usd": 0.0, "tokens": 0, "calls": 0})
            return {k: known[k] + local[k] for k in known}
        stored = self.store.counter(subject, window)
        self.last_known[(subject, window)] = stored
        return {k: stored[k] + local[k] for k in stored}

    def breaker_open(self, provider: str) -> bool:
        """After 3 failures in a row, a provider is not tried for 10 seconds (the estate's clock)."""
        b = self.breakers.get(provider)
        return bool(b and b[1] > clock.now().timestamp())

    def breaker_result(self, provider: str, ok: bool) -> None:
        b = self.breakers.setdefault(provider, [0, 0.0])
        if ok:
            b[0], b[1] = 0, 0.0
        else:
            b[0] += 1
            if b[0] >= 3:
                b[1] = clock.now().timestamp() + 10.0

    def record(self, row: dict, degraded: bool) -> bool:
        """Write the usage row; while the store is down, keep it (and count it here). True if stored."""
        if degraded or self.faults["usage_store"] == "down":
            self.pending.append(row)
            w = windows(row["ts"])
            tokens = int(row.get("tokens_in") or 0) + int(row.get("tokens_out") or 0)
            for subject in (row.get("agent_id"), f"team:{row.get('team')}"):
                for win in w.values():
                    c = self.local.setdefault((subject, win), {"cost_usd": 0.0, "tokens": 0, "calls": 0})
                    c["cost_usd"] += float(row.get("cost_usd") or 0)
                    c["tokens"] += tokens
                    c["calls"] += 1
            return False
        try:
            while self.pending:                     # the store is back: write what waited, then forget the local counts
                self.store.record_model(self.pending[0])
                self.pending.pop(0)
            self.local.clear()
            self.store.record_model(row)
            return True
        except (StoreDown, OSError) as e:
            self.faults["usage_store"] = "down"
            self.pending.append(row)
            raise StoreDown(str(e)) from e


def _err(e: Refused, base: dict) -> JSONResponse:
    return JSONResponse({"error": {"code": e.code, "message": str(e), "type": "gateway", "check": e.check}},
                        e.status, headers={**base, **e.headers})


async def handle(request: Request, endpoint: str) -> JSONResponse:
    rep: Replica = request.app.state.replica
    started = time.perf_counter()
    rid = uuid.uuid4().hex[:16]
    snap = rep.cache.snapshot
    fresh = rep.cache.freshness()
    headers = {"x-gateway-request-id": rid, "x-gateway-replica": rep.name}
    row = {"ts": clock.iso(), "request_id": rid, "replica": rep.name, "outcome": "refused",
           "traceparent": request.headers.get("traceparent"), "run_id": request.headers.get("x-run-id")}
    span = telemetry.start(endpoint)
    degraded = False
    try:
        # 1. Configuration.
        if snap is None:
            raise Refused(503, "control_unavailable", "This gateway replica has no configuration yet.", "configuration")
        row["config_version"] = snap["version"]
        headers["x-gateway-config"] = snap["version"]
        # 2. Identity.
        auth = request.headers.get("authorization", "")
        try:
            claims = rep.verify(snap, auth[7:].strip() if auth.lower().startswith("bearer ") else "")
        except identity.TokenError as e:
            raise Refused(401, e.code, str(e), "identity") from None
        agent_id = claims["sub"]
        row["agent_id"] = agent_id
        # 3. Registration.
        agent = snap["agents"].get(agent_id)
        if agent is None:
            raise Refused(403, "not_registered", f"{agent_id} is not registered: register it before its first call.",
                          "registration")
        row["team"] = agent["team"]
        bad = identity.check_credential(agent, claims)
        if bad:
            raise Refused(401, *bad, "identity")
        if agent["status"] in ("suspended", "retired", "pending"):
            raise Refused(403, f"agent_{agent['status']}",
                          f"{agent_id} is {agent['status']}: the gateway refuses its calls.", "registration")
        if agent["status"] == "draining":
            run_id = row["run_id"]
            seen = None
            with contextlib.suppress(StoreDown):
                seen = rep.store.run_calls(agent_id, run_id) if run_id else None
            if not seen:
                raise Refused(403, "agent_draining", f"{agent_id} is draining: running work may finish, no new run "
                              "may start.", "registration")
        try:
            body = json.loads(await request.body() or b"{}")
        except json.JSONDecodeError:
            raise Refused(400, "invalid_json", "The request body is not valid JSON.", "request") from None
        # 4. Capability.
        cat = snap["catalog"]
        asked = str(body.get("model", ""))
        capability = asked
        if asked in (cat.get("aliases") or {}):
            capability = cat["aliases"][asked]
            headers["x-gateway-warning"] = f"model name {asked} is an old alias of the capability {capability}: ask " \
                                           f"for {capability}"
        row["capability"] = capability
        if capability not in cat["capabilities"]:
            raise Refused(400, "unknown_capability", f"There is no capability {asked!r}. Ask for one of: "
                          f"{', '.join(c for c in cat['capabilities'] if c in agent['capabilities'])}.", "capability")
        if capability not in agent["capabilities"]:
            raise Refused(403, "capability_not_allowed", f"{agent_id}'s registration does not list {capability}.",
                          "capability")
        contract = cat["capabilities"][capability]["contract"]
        want = "embeddings" if endpoint == "embeddings" else "chat"
        if want not in contract.get("features", []):
            raise Refused(400, "wrong_endpoint", f"{capability} does not serve {endpoint}.", "capability")
        if body.get("tools") and "tools" not in contract.get("features", []):
            raise Refused(400, "feature_not_in_contract", f"{capability} does not offer tool calling (its contract "
                          f"has no tools).", "capability")
        if not cat["capabilities"][capability].get("mapping"):
            raise Refused(501, "capability_not_available", f"{capability} is in the catalog, but nothing serves it yet.",
                          "capability")
        # 5. Data class.
        classes = snap["data_classes"]
        dc = request.headers.get("x-data-class") or max(agent["data_classes"] or ["public"],
                                                        key=lambda c: classes.get(c, {}).get("rank", 0))
        row["data_class"] = dc
        if dc not in classes:
            raise Refused(400, "unknown_data_class", f"Unknown data class {dc!r}.", "data_class")
        if classes[dc].get("never_to_a_model"):
            raise Refused(403, "data_class_not_allowed", f"{dc} data is never sent to a model.", "data_class")
        if dc not in agent["data_classes"]:
            raise Refused(403, "data_class_not_allowed", f"{agent_id} is not registered for {dc} data.", "data_class")
        if dc not in contract.get("data_classes", []):
            raise Refused(403, "data_class_not_allowed", f"{capability} does not allow {dc} data.", "data_class")
        # 6. Kill switches.
        stop = switches.blocked(snap, agent_id, capability=capability)
        if stop:
            raise Refused(403, "stopped", f"Stopped: {stop}.", "kill_switch")
        # 7. Failure mode: can every control run?
        tier = agent["risk_tier"]
        mode = agent.get("failure_mode") or snap["settings"]["failure_modes"].get(tier, "fail_closed")
        reasons = []
        if fresh == "expired":
            reasons.append(f"the configuration is {int(rep.cache.age() or 0)} s old (limit "
                           f"{int(rep.cache.max_stale())} s)" if rep.cache.age() is not None else
                           "the configuration came from disk, and the store has not answered since")
        if rep.faults["usage_store"] == "down":
            reasons.append("the usage store is unreachable, so budgets cannot be checked across replicas")
        if reasons:
            if mode == "fail_closed":
                raise Refused(503, "control_unavailable", f"A control cannot run ({'; '.join(reasons)}): {tier} risk "
                              "fails closed.", "failure_mode", {"retry-after": "30"})
            degraded = True
            headers["x-gateway-degraded"] = f"fail open ({tier} risk): " + "; ".join(reasons)
        # 8. Limits.
        lim = agent.get("limits") or {}
        w = windows(row["ts"])
        try:
            minute = rep.counter(agent_id, w["minute"], degraded)
            day = rep.counter(agent_id, w["day"], degraded)
            month = rep.counter(agent_id, w["month"], degraded)
            team_month = rep.counter(f"team:{agent['team']}", w["month"], degraded)
            run_calls = None if (degraded or not row["run_id"]) else rep.store.run_calls(agent_id, row["run_id"])
        except StoreDown:
            rep.faults["usage_store"] = "down"
            raise Refused(503, "control_unavailable", "The usage store is unreachable.", "failure_mode",
                          {"retry-after": "30"}) from None
        if lim.get("requests_per_minute") and minute["calls"] >= lim["requests_per_minute"]:
            raise Refused(429, "rate_limited", f"{agent_id} may send {lim['requests_per_minute']} requests a minute.",
                          "rate_limit", {"retry-after": str(60 - clock.now().second)})
        if lim.get("max_calls_per_run") and row["run_id"] and (run_calls or 0) >= lim["max_calls_per_run"]:
            raise Refused(429, "run_step_limit", f"Run {row['run_id']} has made {run_calls} model calls: the limit is "
                          f"{lim['max_calls_per_run']}. Stop the run and hand the task to a person.", "step_limit")
        if lim.get("tokens_per_day") and day["tokens"] >= lim["tokens_per_day"]:
            raise Refused(429, "quota_exhausted", f"{agent_id} has used its {lim['tokens_per_day']:,} tokens for today.",
                          "quota")
        budget = float(agent.get("budget_usd_month") or 0)
        if budget and month["cost_usd"] >= budget:
            raise Refused(429, "budget_exhausted", f"{agent_id} has spent its US${budget:.2f} for this month.",
                          "budget")
        tbudget = float((snap.get("teams") or {}).get(agent["team"], {}).get("budget_usd_month") or 0)
        if tbudget and team_month["cost_usd"] >= tbudget:
            raise Refused(429, "budget_exhausted", f"The {agent['team']} team has spent its US${tbudget:.2f} for this "
                          "month.", "budget")
        warn_at = float(snap["settings"].get("budgets", {}).get("soft_warning_at", 0.8))
        if budget:
            headers["x-gateway-budget-remaining-usd"] = f"{max(0.0, budget - month['cost_usd']):.4f}"
            if month["cost_usd"] >= warn_at * budget:
                headers["x-gateway-budget-warning"] = f"{agent_id} has used {month['cost_usd'] / budget:.0%} of its " \
                                                      "monthly budget"
        # 9. Guardrails.
        decision, body, notes = guardrails.apply(body, snap["settings"].get("guardrails") or [])
        if notes:
            row["guardrail"] = "; ".join(notes)
        if decision == "block":
            raise Refused(400, "blocked_by_guardrail", f"Blocked by a guardrail: {'; '.join(notes)}.", "guardrail")
        if decision == "redacted":
            headers["x-gateway-redacted"] = "; ".join(notes)
        # 10. Route.
        pin = (agent.get("pins") or {}).get(capability)
        targets = catalog_mod.targets(cat, capability, dc, pin, snap["providers"])
        if not targets:
            raise Refused(503, "no_provider_available", f"No provider may serve {capability} with {dc} data.", "route")
        last = None
        answer = None
        for i, t in enumerate(targets):
            if rep.breaker_open(t.provider):
                last = (503, {"error": {"code": "breaker_open", "message": f"{t.provider} failed 3 times in a row; "
                                        "not tried for 10 s"}}, t)
                continue
            prov = snap["providers"][t.provider]
            url = prov["base_url"].replace("{provsim}", rep.provsim_url) + ("/embeddings" if endpoint == "embeddings"
                                                                             else "/chat/completions")
            up_headers = {"content-type": "application/json", "x-sim-host": f"gateway-{rep.name}"}
            if prov.get("key"):
                up_headers["api-key"] = rep.secrets.get(prov["key"], "")
            for h in ("traceparent", "x-sim-repeat", "x-replay-time"):
                if request.headers.get(h):
                    up_headers[h] = request.headers[h]
            t0 = time.perf_counter()
            try:
                r = await rep.client.post(url, json=t.body_for(body), headers=up_headers)
            except httpx.HTTPError as e:
                rep.breaker_result(t.provider, False)
                last = (503, {"error": {"code": "provider_unreachable", "message": f"{t.label()}: {type(e).__name__}"}}, t)
                continue
            up_ms = (time.perf_counter() - t0) * 1000
            if r.status_code in RETRYABLE:
                rep.breaker_result(t.provider, False)
                last = (r.status_code, r.json(), t)
                continue
            rep.breaker_result(t.provider, True)
            answer = (r, t, up_ms, i > 0)
            break
        if answer is None:
            status, err_body, t = last
            row.update(provider=t.provider, deployment=t.deployment)
            raise Refused(503, "no_provider_available", f"No provider answered for {capability}: last error "
                          f"{status} {err_body.get('error', {}).get('message', '')}".strip(), "route")
        r, t, up_ms, fell_back = answer
        data = r.json()
        model_version = data.get("model", "")
        row.update(provider=t.provider, deployment=t.deployment, model_version=model_version, upstream_ms=round(up_ms, 2),
                   status=r.status_code, fallback=int(fell_back), recorded_ms=float(r.headers.get(
                       "x-sim-recorded-latency-ms") or 0) or None)
        headers.update({"x-gateway-capability": capability, "x-gateway-provider": t.provider,
                        "x-gateway-model": f"{t.deployment} ({model_version})" if model_version else t.deployment})
        for h in ("x-sim-source", "x-sim-match", "x-sim-constructed", "x-sim-recorded-latency-ms"):
            if r.headers.get(h):
                headers[h] = r.headers[h]
        if fell_back:
            headers["x-gateway-fallback"] = f"answered by the fallback {t.label()}"
        if pin and pin.get("model_version") and model_version and model_version != pin["model_version"]:
            raise Refused(502, "pinned_model_changed", f"{agent_id} pins {capability} to {pin['model_version']}, but "
                          f"{t.label()} answered with {model_version}.", "route")
        if r.status_code >= 400:
            row["outcome"] = "upstream_error"
            row["check_name"] = "provider"
            row["message"] = (data.get("error") or {}).get("message", "")[:300]
            headers["x-gateway-upstream-status"] = str(r.status_code)
            row["gateway_ms"] = round((time.perf_counter() - started) * 1000 - up_ms, 2)
            with contextlib.suppress(StoreDown):
                rep.record(row, degraded)
            telemetry.end(span, row)
            return JSONResponse(data, r.status_code, headers=headers)
        usage = data.get("usage") or {}
        price = (snap["models"].get(t.deployment) or {}).get("price") or {}
        row["tokens_in"] = int(usage.get("prompt_tokens") or 0)
        row["tokens_out"] = int(usage.get("completion_tokens") or 0)
        row["cost_usd"] = round((row["tokens_in"] * price.get("input", 0) + row["tokens_out"] * price.get("output", 0))
                                / 1e6, 8)
        row["outcome"] = "ok"
        row["degraded"] = int(degraded)
        headers["x-gateway-cost-usd"] = f"{row['cost_usd']:.6f}"
        row["gateway_ms"] = round((time.perf_counter() - started) * 1000 - up_ms, 2)
        try:
            rep.record(row, degraded)
        except StoreDown:
            headers["x-gateway-degraded"] = "the usage store went down: this call is counted on this replica only"
        telemetry.end(span, row)
        return JSONResponse(data, 200, headers=headers)
    except Refused as e:
        row.update(outcome="refused", status=e.status, check_name=e.check, message=str(e)[:300])
        if e.check in ("route",) and row.get("provider"):
            row["outcome"] = "failed"
        row["gateway_ms"] = round((time.perf_counter() - started) * 1000, 2)
        row["degraded"] = int(degraded)
        with contextlib.suppress(StoreDown, Exception):
            rep.record(row, degraded or rep.faults["usage_store"] == "down")
        telemetry.end(span, row)
        return _err(e, headers)


async def chat(request: Request) -> JSONResponse:
    return await handle(request, "chat")


async def embeddings(request: Request) -> JSONResponse:
    return await handle(request, "embeddings")


async def models(request: Request) -> JSONResponse:
    rep: Replica = request.app.state.replica
    snap = rep.cache.snapshot or {"catalog": {"capabilities": {}}}
    data = [{"id": name, "object": "model", "owned_by": "larkfield-platform",
             "features": cap["contract"].get("features"), "serves": bool(cap.get("mapping"))}
            for name, cap in snap["catalog"]["capabilities"].items()]
    return JSONResponse({"object": "list", "data": data})


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "replica": request.app.state.replica.name})


async def ready(request: Request) -> JSONResponse:
    rep: Replica = request.app.state.replica
    f = rep.cache.freshness()
    body = {"replica": rep.name, "config": (rep.cache.snapshot or {}).get("version"), "freshness": f,
            "age_s": None if rep.cache.age() is None else round(rep.cache.age(), 1), "last_error": rep.cache.last_error,
            "usage_store": rep.faults["usage_store"], "pending_rows": len(rep.pending)}
    return JSONResponse(body, 200 if f != "none" else 503)


async def admin_refresh(request: Request) -> JSONResponse:
    rep: Replica = request.app.state.replica
    ok = await rep.cache.refresh()
    return JSONResponse({"refreshed": ok, "config": (rep.cache.snapshot or {}).get("version")})


async def admin_faults(request: Request) -> JSONResponse:
    """Practice faults on this replica: {"usage_store": "down" | "up"}."""
    rep: Replica = request.app.state.replica
    body = await request.json()
    if body.get("usage_store") in ("down", "up"):
        rep.faults["usage_store"] = body["usage_store"]
        rep.store.down = body["usage_store"] == "down"
    return JSONResponse(rep.faults)


def create_app(replica: str = "a", cache: ConfigCache | None = None, store: UsageStore | None = None,
               secrets: dict | None = None, provsim_url: str | None = None,
               transport: httpx.AsyncBaseTransport | None = None, control_url: str | None = None,
               public_url: str = "") -> Starlette:
    env = os.environ
    control_url = control_url or env.get("ESTATE_URL", "http://127.0.0.1:8321")
    if cache is None:
        async def fetch():
            async with httpx.AsyncClient(timeout=3.0) as c:
                have = (cache.snapshot or {}).get("version", "")
                r = await c.get(f"{control_url}/v1/config", params={"replica": replica, "url": public_url,
                                                                     "have": have})
                r.raise_for_status()
                return r.json()
        cache = ConfigCache(replica, fetch, paths.state() / "gateway" / f"{replica}-config.json")
    if secrets is None:
        sp = paths.state() / "secrets.json"
        secrets = json.loads(sp.read_text()) if sp.exists() else {}
    rep = Replica(replica, cache, store or UsageStore(), secrets,
                  provsim_url or env.get("PROVSIM_URL", "http://127.0.0.1:8320"), transport,
                  float(env.get("GATEWAY_UPSTREAM_TIMEOUT", "60")))

    @contextlib.asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(cache.run()) if cache.fetch else None
        yield
        if task:
            task.cancel()
        await rep.client.aclose()

    app = Starlette(routes=[
        Route("/v1/chat/completions", chat, methods=["POST"]), Route("/v1/embeddings", embeddings, methods=["POST"]),
        Route("/v1/models", models), Route("/health", health), Route("/ready", ready),
        Route("/admin/refresh", admin_refresh, methods=["POST"]), Route("/admin/faults", admin_faults, methods=["POST"]),
    ], lifespan=lifespan)
    app.state.replica = rep
    return app


def secrets_path() -> Path:
    return paths.state() / "secrets.json"
