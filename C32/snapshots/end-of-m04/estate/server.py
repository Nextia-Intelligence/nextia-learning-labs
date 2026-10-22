"""The control plane: the token endpoint, the published keys and the configuration store.

    python -m estate serve [--port 8321]

    POST /oauth/token        client credentials -> a short-lived access token (estate/identity.py)
    GET  /jwks.json          the public key that the gateways use to check tokens
    GET  /v1/config          the configuration snapshot for one replica (estate/configstore.py)
    GET  /v1/rollout         which replica runs which configuration version
    GET  /health

The gateways depend on it only at their next poll: they keep the last snapshot and the keys in memory.
"""

import os

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from estate import configstore, identity, registry

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


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "revision": registry.revision()})


def create_app() -> Starlette:
    return Starlette(routes=[
        Route("/health", health), Route("/jwks.json", jwks), Route("/oauth/token", token, methods=["POST"]),
        Route("/v1/config", config), Route("/v1/rollout", rollout),
    ])


def main(port: int | None = None) -> None:
    import uvicorn

    port = port or int(os.environ.get("ESTATE_PORT", "8321"))
    print(f"Control plane (tokens, keys, configuration) on http://127.0.0.1:{port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")
