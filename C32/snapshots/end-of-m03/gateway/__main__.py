"""Run one replica of the model gateway.

    python -m gateway --replica a [--port 8323]

It needs the control plane (python -m estate serve) for its first configuration; after that it keeps going
with its cached copy when the control plane is down (gateway/config.py).
"""

import argparse
import os

import uvicorn

from gateway import REPLICA_PORTS
from gateway.app import create_app


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m gateway")
    ap.add_argument("--replica", default=os.environ.get("GATEWAY_REPLICA", "a"))
    ap.add_argument("--port", type=int)
    a = ap.parse_args()
    port = a.port or REPLICA_PORTS.get(a.replica, 8323)
    app = create_app(a.replica, public_url=f"http://127.0.0.1:{port}")
    print(f"Model gateway replica {a.replica} on http://127.0.0.1:{port}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
