"""The control plane: the token endpoint, the published keys, the configuration store and the approval service.

    python -m estate serve [--port 8321]

    POST /oauth/token        client credentials -> a short-lived access token (estate/identity.py)
    GET  /jwks.json          the public key that the gateways use to check tokens
    GET  /v1/config          the configuration snapshot for one replica (estate/configstore.py)
    POST /v1/approvals       an approval grant for writes that a person approved (config/policy/approvals.yaml)
    GET  /v1/rollout         which replica runs which configuration version
    GET  /health

The gateways depend on it only at their next poll: they keep the last snapshot and the keys in memory.
"""

import hashlib
import json
import os
import uuid

import jwt
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from estate import clock, configstore, identity, policy, registry

GRANT_SECONDS = 900


def action_digest(tool: str, arguments: dict) -> str:
    """What a person approved: the tool and its exact arguments (the operation ID is not part of the action)."""
    args = {k: v for k, v in (arguments or {}).items() if k != "operation_id"}
    text = json.dumps({"tool": tool, "arguments": args}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status)


async def token(request: Request) -> JSONResponse:
    ctype = request.headers.get("content-type", "")
    form = await request.json() if ctype.startswith("application/json") else dict(await request.form())
    if form.get("grant_type") != "client_credentials":
        return _err(400, "unsupported_grant_type", "Use grant_type=client_credentials.")
    try:
        return JSONResponse(identity.token(form.get("client_id", ""), form.get("client_secret", ""),
                                           form.get("audience", "model-gateway")))
    except identity.TokenError as e:
        return _err(401 if e.code == "invalid_client" else 400, e.code, str(e))


async def jwks(request: Request) -> JSONResponse:
    return JSONResponse(identity.jwks())


async def config(request: Request) -> JSONResponse:
    replica = request.query_params.get("replica", "a")
    try:
        snap = configstore.snapshot(replica)
    except LookupError as e:
        return _err(503, "not_published", str(e))
    configstore.seen(replica, request.query_params.get("url", ""), snap["version"])   # the version it now runs
    return JSONResponse(snap)


async def rollout(request: Request) -> JSONResponse:
    return JSONResponse(configstore.rollout_status())


async def approvals(request: Request) -> JSONResponse:
    """An agent asks for a grant for the actions that a named person approved. The person's role comes from
    config/people.yaml, never from the request. In this practice estate the approver is named in the request
    (a practice shortcut): a real approval service signs the person in first, as the authentication course does."""
    auth = request.headers.get("authorization", "")
    try:
        claims = identity.Verifier(identity.jwks()).verify(auth[7:] if auth.lower().startswith("bearer ") else "",
                                                           "tool-gateway")
    except identity.TokenError as e:
        return _err(401, e.code, str(e))
    body = await request.json()
    approver = body.get("approver", "")
    pol = policy.load()
    actions = body.get("actions") or []
    if not actions:
        return _err(400, "no_actions", "Name the actions that the person approved.")
    if approver == claims["sub"]:
        return _err(403, "approver_not_allowed", "An agent cannot approve its own actions.")
    digests, rules = [], []
    for a in actions:
        d = policy.decide(pol, a["tool"], a.get("arguments") or {}, "write", a.get("data_class"))
        ok, why = policy.may_approve(pol, d, approver)
        if not ok:
            registry_event(claims["sub"], "approval_refused", approver, tool=a["tool"], why=why)
            return _err(403, "approver_not_allowed", why)
        digests.append(action_digest(a["tool"], a.get("arguments") or {}))
        rules.append(d.rule)
    person = registry.people().get(approver, {})
    t = int(clock.now().timestamp())
    grant = {"iss": identity.ISSUER, "sub": claims["sub"], "aud": "tool-gateway", "iat": t, "nbf": t,
             "exp": t + GRANT_SECONDS, "jti": uuid.uuid4().hex, "run_id": body.get("run_id", ""),
             "act": {"sub": approver, "role": person.get("approves")}, "actions": digests, "rules": rules}
    signed = jwt.encode(grant, identity.signing_key(), algorithm="RS256",
                        headers={"kid": identity.kid(), "typ": "approval+jwt"})
    registry_event(claims["sub"], "approval_granted", approver, actions=len(actions), rules=rules,
                   run_id=body.get("run_id", ""))
    return JSONResponse({"grant": signed, "expires_in": GRANT_SECONDS, "rules": rules})


def registry_event(agent_id, action, actor, **detail):
    from contextlib import closing

    with closing(registry.db()) as con, con:
        registry.event(con, agent_id, action, actor, **detail)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "revision": registry.revision()})


def create_app() -> Starlette:
    return Starlette(routes=[
        Route("/health", health), Route("/jwks.json", jwks), Route("/oauth/token", token, methods=["POST"]),
        Route("/v1/config", config), Route("/v1/rollout", rollout), Route("/v1/approvals", approvals, methods=["POST"]),
    ])


def main(port: int | None = None) -> None:
    import uvicorn

    port = port or int(os.environ.get("ESTATE_PORT", "8321"))
    print(f"Control plane (tokens, keys, configuration, approvals) on http://127.0.0.1:{port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")
