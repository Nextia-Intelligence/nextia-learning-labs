"""Kill switches: commands of python -m estate."""

import os

from estate.cli import actor as _actor


def cmd_kill(a):
    from estate import configstore, kill

    if a.scope == "list":
        for k in kill.active():
            print(f"{k['id']:>3}  {k['scope']:<11} {k['target']:<28} {k['created_at']} {k['created_by']}: {k['reason']}")
        return
    if a.scope == "lift":
        kill.lift(int(a.target), _actor(a), a.reason)
        print(f"Kill switch {a.target} lifted.")
    else:
        target = a.target or "*"
        sid = kill.add(a.scope, target, _actor(a), a.reason)
        print(f"Kill switch {sid}: {a.scope} {target} stopped.")
    ok, asked = configstore.push(extra_urls=[os.environ.get("ESTATE_TOOLS_URL", "http://127.0.0.1:8326")])
    print(f"Told {ok} of {asked} gateways to refresh now.")


ORDER = 30


def register(sub) -> dict:
    p = sub.add_parser("kill", help="stop writes, a tool, a capability or everything; list or lift switches")
    p.add_argument("scope", choices=["writes", "tool", "capability", "everything", "list", "lift"])
    p.add_argument("target", nargs="?")
    p.add_argument("--reason", default="")
    p.add_argument("--by")
    return {"kill": cmd_kill}
