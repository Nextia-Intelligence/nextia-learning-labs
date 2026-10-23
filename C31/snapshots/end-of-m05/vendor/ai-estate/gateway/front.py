"""The front door: one address for the gateway, in front of its replicas (a small load balancer).

    python -m gateway.front [--port 8322]      (replicas from GATEWAY_REPLICAS, default a, b and c on 8323-8325)

Apps know one URL. The front door sends each request to the next healthy replica (round robin). It asks every
replica's /ready once a second. A replica that does not answer is taken out until it answers again.

What it retries, and what it does not: if a replica refuses the connection, the request never reached it, so
the front door sends it to the next replica. If a replica dies while it works on a request, the request may
already have reached the provider, so the front door does not send it again: the app gets 502 replica_failed
and decides (a model call is not a write, but it costs money and its answer may differ).

In production this is a managed load balancer with health checks, in more than one zone; this one is small
so that you can see what it does.
"""

import asyncio
import contextlib
import itertools
import os

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from gateway import FRONT_PORT, REPLICA_PORTS

HOP = {"host", "content-length", "connection", "transfer-encoding", "keep-alive"}


def replicas_from_env() -> dict[str, str]:
    spec = os.environ.get("GATEWAY_REPLICAS", "")
    if spec:
        return dict(part.split("=", 1) for part in spec.split(","))
    return {name: f"http://127.0.0.1:{port}" for name, port in REPLICA_PORTS.items()}


class Front:
    def __init__(self, replicas: dict[str, str], transport=None, check_seconds: float = 1.0):
        self.replicas = replicas
        self.healthy = {name: True for name in replicas}
        self.order = itertools.cycle(list(replicas))
        self.client = httpx.AsyncClient(transport=transport, timeout=120.0)
        self.check_seconds = check_seconds
        self.stats = {"sent": 0, "retried_connect": 0, "replica_failed": 0, "no_replica": 0}

    async def check(self) -> None:
        for name, url in self.replicas.items():
            try:
                r = await self.client.get(url + "/ready", timeout=1.0)
                self.healthy[name] = r.status_code == 200
            except httpx.HTTPError:
                self.healthy[name] = False

    async def run(self) -> None:
        while True:
            await self.check()
            await asyncio.sleep(self.check_seconds)

    def next_healthy(self, tried: set) -> str | None:
        for _ in range(len(self.replicas)):
            name = next(self.order)
            if self.healthy.get(name) and name not in tried:
                return name
        return None


async def forward(request: Request) -> Response:
    front: Front = request.app.state.front
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP}
    tried: set = set()
    while True:
        name = front.next_healthy(tried)
        if name is None:
            front.stats["no_replica"] += 1
            return JSONResponse({"error": {"code": "no_replica", "message": "No gateway replica is healthy.",
                                           "type": "front"}}, 503)
        tried.add(name)
        try:
            r = await front.client.request(request.method, front.replicas[name] + request.url.path,
                                           params=request.query_params, content=body, headers=headers)
        except httpx.ConnectError:
            front.healthy[name] = False            # it never got the request: try the next replica
            front.stats["retried_connect"] += 1
            continue
        except httpx.HTTPError as e:
            front.healthy[name] = False            # it got the request and died: do not send it again
            front.stats["replica_failed"] += 1
            return JSONResponse({"error": {"code": "replica_failed", "message": f"Replica {name} failed during the "
                                           f"request ({type(e).__name__}); it was not sent again.", "type": "front"}},
                                502, headers={"x-front-replica": name})
        front.stats["sent"] += 1
        out = {k: v for k, v in r.headers.items() if k.lower() not in HOP | {"content-encoding"}}
        out["x-front-replica"] = name
        return Response(r.content, r.status_code, headers=out)


async def front_status(request: Request) -> JSONResponse:
    front: Front = request.app.state.front
    return JSONResponse({"replicas": front.replicas, "healthy": front.healthy, "stats": front.stats})


def create_app(replicas: dict[str, str] | None = None, transport=None, check_seconds: float = 1.0) -> Starlette:
    front = Front(replicas or replicas_from_env(), transport, check_seconds)

    @contextlib.asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(front.run())
        yield
        task.cancel()
        await front.client.aclose()

    app = Starlette(routes=[Route("/front/status", front_status),
                            Route("/{path:path}", forward, methods=["GET", "POST"])], lifespan=lifespan)
    app.state.front = front
    return app


def main() -> None:
    import argparse

    import uvicorn

    ap = argparse.ArgumentParser(prog="python -m gateway.front")
    ap.add_argument("--port", type=int, default=int(os.environ.get("GATEWAY_PORT", FRONT_PORT)))
    a = ap.parse_args()
    app = create_app()
    print(f"Gateway front door on http://127.0.0.1:{a.port} -> {', '.join(app.state.front.replicas.values())}",
          flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
