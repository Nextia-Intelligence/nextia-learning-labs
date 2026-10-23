"""Run the provider simulator, or read its bill, egress log and controls.

    python -m provsim [--port 8320] [--speed 0] [--egress open|gateway-only]
    python -m provsim bill [--month 2026-10] [--provider fernway]
    python -m provsim egress
    python -m provsim control azure down [--deployment chat-small] [--requests 20]
    python -m provsim control azure normal
"""

import argparse
import json
import os
import sys
import urllib.request

from provsim import DEFAULT_PORT


def _url(port: int, path: str) -> str:
    return f"http://127.0.0.1:{port}{path}"


def _get(port: int, path: str) -> str:
    with urllib.request.urlopen(_url(port, path), timeout=10) as r:
        return r.read().decode("utf-8")


def _post(port: int, path: str, body: dict) -> dict:
    req = urllib.request.Request(_url(port, path), data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m provsim")
    ap.add_argument("--port", type=int, default=int(os.environ.get("SIM_PORT", DEFAULT_PORT)))
    ap.add_argument("--speed", type=float, help="recorded latency x SPEED (0: answer at once; 1: real time)")
    ap.add_argument("--egress", choices=["open", "gateway-only"])
    sub = ap.add_subparsers(dest="command")
    p = sub.add_parser("bill")
    p.add_argument("--month", default="")
    p.add_argument("--provider", default="")
    sub.add_parser("egress")
    sub.add_parser("status")
    p = sub.add_parser("control")
    p.add_argument("provider")
    p.add_argument("mode", choices=["down", "slow", "errors", "rate_limit", "normal"])
    p.add_argument("--deployment")
    p.add_argument("--requests", type=int)
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--rate", type=float, default=0.5)
    a = ap.parse_args(argv)
    try:
        if a.command == "bill":
            print(_get(a.port, f"/admin/bill?month={a.month}&provider={a.provider}"), end="")
        elif a.command == "egress":
            print(_get(a.port, "/admin/egress"), end="")
        elif a.command == "status":
            print(json.dumps(json.loads(_get(a.port, "/admin/settings")), indent=1))
        elif a.command == "control":
            out = _post(a.port, "/admin/control", {"provider": a.provider, "mode": a.mode, "deployment": a.deployment,
                                                   "requests": a.requests, "seconds": a.seconds, "rate": a.rate})
            print(f"Controls now: {json.dumps(out['controls'])} (simulated)")
        else:
            import uvicorn

            from provsim.app import create_app

            app = create_app(speed=a.speed, egress=a.egress)
            print(f"Provider simulator on http://127.0.0.1:{a.port} | {len(app.state.sim.store)} recorded answers | "
                  f"speed {app.state.sim.speed} | egress {app.state.sim.egress}", flush=True)
            uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
    except OSError as e:
        sys.exit(f"Cannot reach the provider simulator on port {a.port}: {e}. Start it with: python -m provsim")


if __name__ == "__main__":
    main()
