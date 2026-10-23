"""The model gateway, first version: one door that refuses every call without a valid registration.

    POST /v1/chat/completions    POST /v1/embeddings    GET /v1/models

It speaks the OpenAI-compatible API, so an app changes its base URL and its credential, and asks for a
capability instead of a model. Every request passes these checks, in this order; the first one that fails
answers:

    1 configuration   the gateway has a snapshot of the registry and the catalog   503 control_unavailable
    2 identity        a valid access token for the model gateway                   401 invalid_token, ...
    3 registration    the agent is registered and active                           403 not_registered, agent_suspended
    4 capability      it asks for a capability that its registration lists         400/403 capability_...
    5 route           the mapping's primary deployment, then its fallbacks         503 no_provider_available

The answer is the provider's, with headers that name the capability and the model that answered.
(The next module adds the usage record, limits, data classes, guardrails and the failure modes.)
"""

import asyncio
import contextlib
import json
import os
import uuid

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from estate import catalog as catalog_mod
from estate import clock, identity, paths
from gateway.config import ConfigCache

RETRYABLE = {429, 500, 502, 503, 504}


class Refused(Exception):
    def __init__(self, status: int, code: str, message: str, check: str):
        super().__init__(message)
        self.status, self.code, self.check = status, code, check


class Replica:
    def __init__(self, name: str, cache: ConfigCache, secrets: dict, provsim_url: str,
                 transport: httpx.AsyncBaseTransport | None = None, timeout: float = 60.0):
        self.name = name
        self.cache = cache
        self.secrets = secrets
        self.provsim_url = provsim_url.rstrip("/")
        self.client = httpx.AsyncClient(transport=transport, timeout=timeout)
        self.verifier_kid = None
        self.verifier: identity.Verifier | None = None

    def verify(self, snap: dict, token: str) -> dict:
        jw = snap.get("jwks") or {"keys": []}
        kid = ",".join(k["kid"] for k in jw["keys"])
        if self.verifier is None or kid != self.verifier_kid:
            self.verifier, self.verifier_kid = identity.Verifier(jw), kid
        return self.verifier.verify(token, "model-gateway", now=clock.now().timestamp())


async def handle(request: Request, endpoint: str) -> JSONResponse:
    rep: Replica = request.app.state.replica
    snap = rep.cache.snapshot
    headers = {"x-gateway-request-id": uuid.uuid4().hex[:16], "x-gateway-replica": rep.name}
    try:
        # 1. Configuration.
        if snap is None:
            raise Refused(503, "control_unavailable", "The gateway has no configuration yet.", "configuration")
        headers["x-gateway-config"] = snap["version"]
        # 2. Identity.
        auth = request.headers.get("authorization", "")
        try:
            claims = rep.verify(snap, auth[7:].strip() if auth.lower().startswith("bearer ") else "")
        except identity.TokenError as e:
            raise Refused(401, e.code, str(e), "identity") from None
        agent_id = claims["sub"]
        # 3. Registration.
        agent = snap["agents"].get(agent_id)
        if agent is None:
            raise Refused(403, "not_registered", f"{agent_id} is not registered: register it before its first call.",
                          "registration")
        bad = identity.check_credential(agent, claims)
        if bad:
            raise Refused(401, *bad, "identity")
        if agent["status"] != "active":
            raise Refused(403, f"agent_{agent['status']}",
                          f"{agent_id} is {agent['status']}: the gateway refuses its calls.", "registration")
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
        if capability not in cat["capabilities"]:
            raise Refused(400, "unknown_capability", f"There is no capability {asked!r}. Ask for one of: "
                          f"{', '.join(c for c in cat['capabilities'] if c in agent['capabilities'])}.", "capability")
        if capability not in agent["capabilities"]:
            raise Refused(403, "capability_not_allowed", f"{agent_id}'s registration does not list {capability}.",
                          "capability")
        # 5. Route: the primary, then the fallbacks; a request error (4xx) is not sent elsewhere.
        targets = catalog_mod.targets(cat, capability, "personal", (agent.get("pins") or {}).get(capability),
                                      snap["providers"])
        last = None
        for i, t in enumerate(targets):
            prov = snap["providers"][t.provider]
            url = prov["base_url"].replace("{provsim}", rep.provsim_url) + ("/embeddings" if endpoint == "embeddings"
                                                                             else "/chat/completions")
            up = {"content-type": "application/json", "x-sim-host": f"gateway-{rep.name}"}
            if prov.get("key"):
                up["api-key"] = rep.secrets.get(prov["key"], "")
            for h in ("traceparent", "x-sim-repeat"):
                if request.headers.get(h):
                    up[h] = request.headers[h]
            try:
                r = await rep.client.post(url, json=t.body_for(body), headers=up)
            except httpx.HTTPError as e:
                last = f"{t.label()}: {type(e).__name__}"
                continue
            if r.status_code in RETRYABLE:
                last = f"{t.label()}: HTTP {r.status_code}"
                continue
            data = r.json()
            headers.update({"x-gateway-capability": capability, "x-gateway-provider": t.provider,
                            "x-gateway-model": f"{t.deployment} ({data.get('model', '')})"})
            if i > 0:
                headers["x-gateway-fallback"] = f"answered by the fallback {t.label()}"
            for h in ("x-sim-source", "x-sim-match", "x-sim-constructed"):
                if r.headers.get(h):
                    headers[h] = r.headers[h]
            return JSONResponse(data, r.status_code, headers=headers)
        raise Refused(503, "no_provider_available", f"No provider answered for {capability}: {last}.", "route")
    except Refused as e:
        return JSONResponse({"error": {"code": e.code, "message": str(e), "type": "gateway", "check": e.check}},
                            e.status, headers=headers)


async def chat(request: Request) -> JSONResponse:
    return await handle(request, "chat")


async def embeddings(request: Request) -> JSONResponse:
    return await handle(request, "embeddings")


async def models(request: Request) -> JSONResponse:
    snap = request.app.state.replica.cache.snapshot or {"catalog": {"capabilities": {}}}
    return JSONResponse({"object": "list", "data": [{"id": n, "object": "model"} for n in snap["catalog"]["capabilities"]]})


async def ready(request: Request) -> JSONResponse:
    rep: Replica = request.app.state.replica
    f = rep.cache.freshness()
    return JSONResponse({"replica": rep.name, "config": (rep.cache.snapshot or {}).get("version"), "freshness": f},
                        200 if f != "none" else 503)


async def admin_refresh(request: Request) -> JSONResponse:
    rep: Replica = request.app.state.replica
    return JSONResponse({"refreshed": await rep.cache.refresh(), "config": (rep.cache.snapshot or {}).get("version")})


def create_app(replica: str = "a", cache: ConfigCache | None = None, store=None, secrets: dict | None = None,
               provsim_url: str | None = None, transport: httpx.AsyncBaseTransport | None = None,
               control_url: str | None = None, public_url: str = "") -> Starlette:
    env = os.environ
    control_url = control_url or env.get("ESTATE_URL", "http://127.0.0.1:8321")
    if cache is None:
        async def fetch():
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{control_url}/v1/config", params={"replica": replica, "url": public_url})
                r.raise_for_status()
                return r.json()
        cache = ConfigCache(replica, fetch, paths.state() / "gateway" / f"{replica}-config.json")
    if secrets is None:
        sp = paths.state() / "secrets.json"
        secrets = json.loads(sp.read_text()) if sp.exists() else {}
    rep = Replica(replica, cache, secrets, provsim_url or env.get("PROVSIM_URL", "http://127.0.0.1:8320"), transport)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(cache.run()) if cache.fetch else None
        yield
        if task:
            task.cancel()
        await rep.client.aclose()

    app = Starlette(routes=[
        Route("/v1/chat/completions", chat, methods=["POST"]), Route("/v1/embeddings", embeddings, methods=["POST"]),
        Route("/v1/models", models), Route("/ready", ready), Route("/health", ready),
        Route("/admin/refresh", admin_refresh, methods=["POST"]),
    ], lifespan=lifespan)
    app.state.replica = rep
    return app
