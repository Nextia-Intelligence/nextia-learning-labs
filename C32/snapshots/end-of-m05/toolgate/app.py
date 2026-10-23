"""The tool gateway: MCP servers behind one door, with the agent's identity on every call.

    GET  /v1/tools          the tools this agent may call (its registration, the platform's tool list, and
                            what the servers really offer)
    POST /v1/tools/call     {"tool": "orders.get_order", "arguments": {...}, "context": {...},
                             "approval": "<grant>", "run_id": "..."}

The model gateway sees model calls, not the agent's actions. The actions are tool calls, so they need their
own door. For every call, in this order:

    1 identity        a valid access token for the tool gateway              401
    2 registration    the agent is registered and active (draining: its running run only)   403
    3 tool allowed    the registration lists server.tool                     403 tool_not_allowed
    4 known tool      the platform lists it (config/tools.yaml: read or write) and the server offers it   404
    5 kill switches   the tool, writes, or everything stopped                403 stopped
    6 arguments       the server's schema, strictly: no extra arguments, size limit   400 invalid_arguments
    7 policy          a write: config/policy/approvals.yaml; an approval grant signed by the control plane
                      for exactly this action, when the policy asks for one   403 approval_required, ...
    8 call            the MCP server, with the customer and the ticket in the request's _meta (never an argument)
    9 record          one row in the usage store (no argument values: a digest)

It talks MCP to the servers (the official SDK's client on stdio). The agents talk plain JSON over HTTP to it.
"""

import asyncio
import contextlib
import hashlib
import json
import os
import sys
import time
import uuid

import httpx
import jsonschema
import jwt
import yaml
from mcp import Client, StdioServerParameters
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from estate import clock, identity, paths, policy, switches
from estate.server import action_digest
from estate.usage import StoreDown, UsageStore
from gateway.config import ConfigCache
from orders_mcp import CONTEXT_KEY


class Refused(Exception):
    def __init__(self, status: int, code: str, message: str, check: str):
        super().__init__(message)
        self.status, self.code, self.check = status, code, check


class Backend:
    """One MCP server, started on stdio, with its discovered tools."""

    def __init__(self, name: str, spec: dict):
        self.name = name
        self.spec = spec
        self.client: Client | None = None
        self.tools: dict[str, dict] = {}
        self.lock = asyncio.Lock()

    def params(self) -> StdioServerParameters:
        cmd = [sys.executable if c == "{python}" else c for c in self.spec["command"]]
        env = {**os.environ, **(self.spec.get("env") or {})}
        return StdioServerParameters(command=cmd[0], args=cmd[1:], env=env, cwd=str(paths.PROJECT))

    async def start(self, stack: contextlib.AsyncExitStack) -> None:
        self.client = await stack.enter_async_context(Client(self.params()))
        listed = await self.client.list_tools()
        self.tools = {t.name: t.input_schema for t in listed.tools}

    async def call(self, tool: str, arguments: dict, meta: dict) -> tuple[bool, object]:
        async with self.lock:
            r = await self.client.call_tool(tool, arguments, meta=meta)
        text = "".join(getattr(c, "text", "") for c in r.content)
        sc = r.structured_content
        if isinstance(sc, dict) and set(sc) == {"result"} and isinstance(sc["result"], str):
            text = sc["result"]           # a tool that returns a JSON string (orders-mcp)
        elif sc:
            return (not r.is_error), sc    # a tool with an output schema (support-mcp)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"text": text}
        return (not r.is_error), data


class ToolGateway:
    def __init__(self, cache: ConfigCache, store: UsageStore, servers: dict):
        self.cache = cache
        self.store = store
        self.servers = servers                      # config/tools.yaml "servers"
        self.backends: dict[str, Backend] = {}
        self.verifier = None
        self.verifier_kid = None

    def verify(self, token: str, audience: str = "tool-gateway") -> dict:
        jw = (self.cache.snapshot or {}).get("jwks") or {"keys": []}
        kid = ",".join(k["kid"] for k in jw["keys"])
        if self.verifier is None or kid != self.verifier_kid:
            self.verifier, self.verifier_kid = identity.Verifier(jw), kid
        return self.verifier.verify(token, audience, now=clock.now().timestamp())

    def verify_grant(self, grant: str, agent_id: str, tool: str, arguments: dict, needs: str, pol: dict) -> dict:
        if not grant:
            raise Refused(403, "approval_required", f"{tool} needs a person's approval ({needs.replace('_', ' ')} or "
                          "above): send the approval grant from the control plane.", "policy")
        try:
            header = jwt.get_unverified_header(grant)
            keys = {k["kid"]: k for k in ((self.cache.snapshot or {}).get("jwks") or {"keys": []})["keys"]}
            if header.get("typ") != "approval+jwt" or header.get("kid") not in keys:
                raise jwt.InvalidTokenError("not an approval grant of this estate")
            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(keys[header["kid"]]))
            # The times are checked below against the estate's clock (a replayed month moves it).
            claims = jwt.decode(grant, key, algorithms=["RS256"], audience="tool-gateway", issuer=identity.ISSUER,
                                options={"verify_exp": False, "verify_nbf": False, "verify_iat": False})
        except jwt.PyJWTError as e:
            raise Refused(403, "approval_invalid", f"The approval grant is not valid ({type(e).__name__}).",
                          "policy") from None
        if claims["exp"] < clock.now().timestamp():
            raise Refused(403, "approval_invalid", "The approval grant has expired: ask the person again.", "policy")
        if claims["sub"] != agent_id:
            raise Refused(403, "approval_invalid", "The approval grant is for another agent.", "policy")
        if action_digest(tool, arguments) not in claims.get("actions", []):
            raise Refused(403, "approval_invalid", "The approval grant does not cover this exact action (tool and "
                          "arguments).", "policy")
        if policy.role_rank(pol, claims["act"].get("role")) < policy.role_rank(pol, needs):
            raise Refused(403, "approval_invalid", f"{claims['act']['sub']} may not approve this: it needs a "
                          f"{needs.replace('_', ' ')} or above.", "policy")
        return claims


async def call_tool(request: Request) -> JSONResponse:
    tg: ToolGateway = request.app.state.tg
    started = time.perf_counter()
    rid = uuid.uuid4().hex[:16]
    snap = tg.cache.snapshot
    row = {"ts": clock.iso(), "request_id": rid, "outcome": "refused"}
    try:
        if snap is None:
            raise Refused(503, "control_unavailable", "The tool gateway has no configuration yet.", "configuration")
        auth = request.headers.get("authorization", "")
        try:
            claims = tg.verify(auth[7:].strip() if auth.lower().startswith("bearer ") else "")
        except identity.TokenError as e:
            raise Refused(401, e.code, str(e), "identity") from None
        agent_id = claims["sub"]
        row["agent_id"] = agent_id
        agent = snap["agents"].get(agent_id)
        if agent is None:
            raise Refused(403, "not_registered", f"{agent_id} is not registered.", "registration")
        row["team"] = agent["team"]
        bad = identity.check_credential(agent, claims)
        if bad:
            raise Refused(401, *bad, "identity")
        body = await request.json()
        full = str(body.get("tool", ""))
        row["run_id"] = body.get("run_id")
        server, _, tool = full.partition(".")
        row.update(server=server, tool=tool)
        if agent["status"] in ("suspended", "retired", "pending"):
            raise Refused(403, f"agent_{agent['status']}", f"{agent_id} is {agent['status']}.", "registration")
        if agent["status"] == "draining":
            seen = tg.store.rows("select 1 from tool_calls where agent_id = ? and run_id = ? and outcome = 'ok' "
                                 "limit 1", (agent_id, row["run_id"])) if row["run_id"] else []
            if not seen:
                raise Refused(403, "agent_draining", f"{agent_id} is draining: no new run may start.", "registration")
        if full not in agent["tools"]:
            raise Refused(403, "tool_not_allowed", f"{agent_id}'s registration does not allow {full}.", "tool")
        spec = (snap["tools"]["servers"].get(server) or {}).get("tools", {}).get(tool)
        backend = tg.backends.get(server)
        if spec is None or backend is None or tool not in backend.tools:
            raise Refused(404, "unknown_tool", f"The platform has no tool {full}.", "tool")
        kind = spec["kind"]
        row["kind"] = kind
        stop = switches.blocked(snap, agent_id, tool=full, write=kind == "write")
        if stop:
            raise Refused(403, "stopped", f"Stopped: {stop}.", "kill_switch")
        arguments = body.get("arguments") or {}
        text = json.dumps(arguments, sort_keys=True)
        row["args_digest"] = hashlib.sha256(text.encode()).hexdigest()[:16]
        if len(text) > int(snap["tools"].get("max_argument_chars", 2000)):
            raise Refused(400, "invalid_arguments", "The arguments are too long.", "arguments")
        schema = backend.tools[tool]
        extra = set(arguments) - set((schema.get("properties") or {}))
        if extra:   # the server's schema allows extra arguments (no additionalProperties: false): the gateway does not
            raise Refused(400, "invalid_arguments", f"Unknown arguments for {full}: {', '.join(sorted(extra))}.",
                          "arguments")
        try:
            jsonschema.validate(arguments, schema)
        except jsonschema.ValidationError as e:
            raise Refused(400, "invalid_arguments", f"Invalid arguments for {full}: {e.message}", "arguments") from None
        pol = snap["policy"]
        decision = policy.decide(pol, full, arguments, kind)
        row["rule"] = decision.rule
        if decision.denied:
            raise Refused(403, "policy_denied", f"The policy refuses {full} (rule {decision.rule}).", "policy")
        if decision.needs:
            grant = tg.verify_grant(body.get("approval", ""), agent_id, full, arguments, decision.needs, pol)
            row["approver"] = grant["act"]["sub"]
        ctx = body.get("context") or {}
        meta = {CONTEXT_KEY: {**ctx, "agent_id": agent_id}}
        try:
            ok, data = await backend.call(tool, arguments, meta)
        except Exception as e:   # the server crashed or timed out
            raise Refused(502, "server_failed", f"{server} failed: {type(e).__name__}.", "server") from None
        row["outcome"] = "ok" if ok else "tool_error"
        row["status"] = 200
        row["ms"] = round((time.perf_counter() - started) * 1000, 2)
        with contextlib.suppress(StoreDown):
            tg.store.record_tool(row)
        return JSONResponse({"ok": ok, "result": data, "request_id": rid},
                            headers={"x-toolgate-request-id": rid, "x-toolgate-rule": decision.rule})
    except Refused as e:
        row.update(status=e.status, check_name=e.check, message=str(e)[:300])
        row["ms"] = round((time.perf_counter() - started) * 1000, 2)
        with contextlib.suppress(StoreDown, Exception):
            tg.store.record_tool(row)
        return JSONResponse({"error": {"code": e.code, "message": str(e), "check": e.check}}, e.status,
                            headers={"x-toolgate-request-id": rid})


async def list_tools(request: Request) -> JSONResponse:
    tg: ToolGateway = request.app.state.tg
    auth = request.headers.get("authorization", "")
    try:
        claims = tg.verify(auth[7:].strip() if auth.lower().startswith("bearer ") else "")
    except identity.TokenError as e:
        return JSONResponse({"error": {"code": e.code, "message": str(e)}}, 401)
    agent = (tg.cache.snapshot or {}).get("agents", {}).get(claims["sub"]) or {"tools": []}
    out = []
    for name, b in tg.backends.items():
        for tool in b.tools:
            full = f"{name}.{tool}"
            spec = tg.servers.get(name, {}).get("tools", {}).get(tool)
            if spec and full in agent["tools"]:
                out.append({"tool": full, "kind": spec["kind"]})
    return JSONResponse({"agent": claims["sub"], "tools": out})


async def ready(request: Request) -> JSONResponse:
    tg: ToolGateway = request.app.state.tg
    return JSONResponse({"config": (tg.cache.snapshot or {}).get("version"), "freshness": tg.cache.freshness(),
                         "servers": {n: sorted(b.tools) for n, b in tg.backends.items()}})


async def admin_refresh(request: Request) -> JSONResponse:
    tg: ToolGateway = request.app.state.tg
    return JSONResponse({"refreshed": await tg.cache.refresh(), "config": (tg.cache.snapshot or {}).get("version")})


def create_app(cache: ConfigCache | None = None, store: UsageStore | None = None, servers: dict | None = None,
               control_url: str | None = None, start_backends: bool = True) -> Starlette:
    control_url = control_url or os.environ.get("ESTATE_URL", "http://127.0.0.1:8321")
    servers = servers or yaml.safe_load((paths.CONFIG / "tools.yaml").read_text())["servers"]
    if cache is None:
        async def fetch():
            async with httpx.AsyncClient(timeout=3.0) as c:
                r = await c.get(f"{control_url}/v1/config", params={"replica": "tools"})
                r.raise_for_status()
                return r.json()
        cache = ConfigCache("tools", fetch, paths.state() / "gateway" / "tools-config.json")
    tg = ToolGateway(cache, store or UsageStore(), servers)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            if start_backends:
                for name, spec in servers.items():
                    b = Backend(name, spec)
                    await b.start(stack)
                    tg.backends[name] = b
            task = asyncio.create_task(cache.run()) if cache.fetch else None
            yield
            if task:
                task.cancel()

    app = Starlette(routes=[Route("/v1/tools", list_tools), Route("/v1/tools/call", call_tool, methods=["POST"]),
                            Route("/ready", ready), Route("/health", ready),
                            Route("/admin/refresh", admin_refresh, methods=["POST"])], lifespan=lifespan)
    app.state.tg = tg
    return app
