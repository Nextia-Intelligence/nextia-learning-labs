"""Start the run inspector: python -m larkfield_inspector (or the command larkfield-inspector).

    larkfield-inspector                     saved mode: the built-in replayed week, no setup
    larkfield-inspector --data DIR          also open your own saved telemetry (a folder with traces.jsonl)
    INSPECTOR_MODE=live larkfield-inspector live mode: Tempo, Prometheus and the audit store file (read-only)
    larkfield-inspector --no-browser        do not open the browser
"""

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__
from .server import Inspector, make_server, static_folder


def main(argv=None) -> int:
    env = os.environ
    ap = argparse.ArgumentParser(prog="larkfield-inspector",
                                 description="A read-only view of AI agent runs: runs, one run, audit, cost, compare.")
    ap.add_argument("--port", type=int, default=int(env.get("INSPECTOR_PORT", "8318")))
    ap.add_argument("--host", default=env.get("INSPECTOR_HOST", "127.0.0.1"),
                    help="the address to listen on (default 127.0.0.1: this computer only)")
    ap.add_argument("--mode", choices=["saved", "live"], default=env.get("INSPECTOR_MODE", "saved"))
    ap.add_argument("--data", default=env.get("INSPECTOR_DATA"), help="a folder of your own saved telemetry")
    ap.add_argument("--no-browser", action="store_true", default=env.get("INSPECTOR_NO_BROWSER") == "1")
    ap.add_argument("--version", action="version", version=f"larkfield-inspector {__version__}")
    args = ap.parse_args(argv)

    if args.data and not (Path(args.data) / "traces.jsonl").exists() and not (Path(args.data) / "traces.jsonl.gz").exists():
        print(f"No traces.jsonl in {args.data}.", file=sys.stderr)
        return 2
    app = Inspector(args.mode, env, Path(args.data) if args.data else None)
    try:
        server = make_server(app, args.host, args.port)
    except OSError as e:
        print(f"Cannot listen on {args.host}:{args.port} ({e.strerror}). Another program uses the port? "
              f"Try --port {args.port + 1}, or set INSPECTOR_PORT.", file=sys.stderr)
        return 1
    shown_host = "127.0.0.1" if args.host in ("0.0.0.0", "") else args.host
    url = f"http://{shown_host}:{args.port}/"
    if args.mode == "live":
        what = (f"live mode: Tempo {env.get('TEMPO_URL', 'http://127.0.0.1:3200')}, "
                f"Prometheus {env.get('PROMETHEUS_URL', 'http://127.0.0.1:9090')}, "
                f"audit store {env.get('AUDIT_STORE') or '(not set)'}; read-only")
    else:
        what = "saved mode: the built-in replayed week"
    print(f"Run inspector {__version__} on {url} ({what}).", flush=True)
    print("The saved data is a replayed week: real recorded model decisions from the agents course, "
          "constructed traffic and practice incidents. No data leaves this computer.", flush=True)
    if static_folder() is None:
        print("The web pages (web/dist) are missing: only the API answers.", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
