"""Run the tool gateway: python -m toolgate [--port 8326]. It starts the MCP servers of config/tools.yaml."""

import argparse
import os

import uvicorn

from toolgate import DEFAULT_PORT
from toolgate.app import create_app


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m toolgate")
    ap.add_argument("--port", type=int, default=int(os.environ.get("TOOLGATE_PORT", DEFAULT_PORT)))
    a = ap.parse_args()
    print(f"Tool gateway on http://127.0.0.1:{a.port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
