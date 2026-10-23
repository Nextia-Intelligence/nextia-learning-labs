"""Start and stop the estate: commands of python -m estate."""

import shutil
import sys

from estate import paths


def cmd_init(a):
    st = paths.state()
    print(f"State folder: {st}")
    print("The estate has no platform yet: each app calls the provider with its own key.")


def cmd_up(a):
    from estate import services

    for line in services.up(a.only):
        print(line)


def cmd_down(a):
    from estate import services

    lines = services.down(a.only)
    print("\n".join(lines) or "Nothing was running.")


def cmd_status(a):
    from estate import services

    print("\n".join(services.status()))


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
    p = sub.add_parser("init", help="create the state folder")
    p.add_argument("--by")
    p = sub.add_parser("up", help="start the estate's services")
    p.add_argument("only", nargs="*")
    p.add_argument("--by")
    p = sub.add_parser("down", help="stop the services that up started")
    p.add_argument("only", nargs="*")
    sub.add_parser("status", help="which services run, and what they answer")
    sub.add_parser("reset", help="delete the practice state (stop the services first)")
    return {"init": cmd_init, "up": cmd_up, "down": cmd_down, "status": cmd_status, "reset": cmd_reset}
