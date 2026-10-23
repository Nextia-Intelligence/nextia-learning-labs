"""Start and stop the estate: commands of python -m estate."""

import json
import shutil
import sys

from estate import paths
from estate.cli import actor as _actor


def cmd_init(a):
    from estate import configstore, identity

    st = paths.state()
    secrets = st / "secrets.json"
    if not secrets.exists():
        secrets.write_text(json.dumps({"azure": "sim-az-gateway-0009"}, indent=1) + "\n")
        secrets.chmod(0o600)
    identity.signing_key()
    try:
        v = configstore.version_for("a")
    except Exception:
        v = None
    if v is None:
        v = configstore.publish(_actor(a), "first configuration")
        print(f"Published configuration version {v}.")
    print(f"State folder: {st}")
    print("The gateway's provider key is in state/secrets.json (only the gateway reads it).")
    print("The signing key of the estate's tokens is in state/identity/ (only the control plane reads it).")


def cmd_up(a):
    from estate import services

    if not (paths.state() / "secrets.json").exists():
        cmd_init(a)
    for line in services.up(a.only):
        print(line)


def cmd_down(a):
    from estate import services

    lines = services.down(a.only)
    print("\n".join(lines) or "Nothing was running.")


def cmd_status(a):
    from estate import services

    print("\n".join(services.status()))


def cmd_serve(a):
    from estate import server

    server.main(a.port)


def cmd_reset(a):
    from estate import services

    if services.running():
        sys.exit("Stop the services first: python -m estate down")
    st = paths.state()
    shutil.rmtree(st, ignore_errors=True)
    print(f"Deleted {st} (the registry, the usage records, the keys and the practice database). "
          "Start again with: python -m estate init")


ORDER = 0


def register(sub) -> dict:
    p = sub.add_parser("init", help="create the state folder, the keys and the first configuration")
    p.add_argument("--by")
    p = sub.add_parser("up", help="start the estate's services")
    p.add_argument("only", nargs="*")
    p.add_argument("--by")
    p = sub.add_parser("down", help="stop the services that up started")
    p.add_argument("only", nargs="*")
    sub.add_parser("status", help="which services run, and what they answer")
    p = sub.add_parser("serve", help="run the control plane (up does it for you)")
    p.add_argument("--port", type=int)
    sub.add_parser("reset", help="delete the practice state (stop the services first)")
    return {"init": cmd_init, "up": cmd_up, "down": cmd_down, "status": cmd_status, "serve": cmd_serve,
            "reset": cmd_reset}
