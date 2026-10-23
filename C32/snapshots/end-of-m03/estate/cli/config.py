"""The configuration store: commands of python -m estate."""

import sys

from estate.cli import actor as _actor


def cmd_config(a):
    from estate import configstore

    if a.action == "check":
        problems = configstore.validate(configstore.gather())
        print("\n".join(problems) if problems else "The configuration is valid.")
        sys.exit(1 if problems else 0)
    if a.action == "status":
        s = configstore.rollout_status()
        print(f"version {s['stable']}")
        for r in s["replicas"]:
            print(f"  replica {r['replica']:<6} runs {r['version']:<10} last seen {r['last_seen']}")
        for v in s["versions"][-5:]:
            print(f"  v{v['version']} {v['digest']} {v['created_at']} {v['created_by']}: {v['note']}")
        return
    try:
        v = configstore.publish(_actor(a), a.note or "")
        print(f"Published version {v}.")
    except ValueError as e:
        sys.exit(str(e))
    ok, asked = configstore.push()
    if asked:
        print(f"Told {ok} of {asked} gateways to refresh now.")


ORDER = 22


def register(sub) -> dict:
    p = sub.add_parser("config", help="publish or check the configuration, or see which version runs")
    p.add_argument("action", choices=["publish", "status", "check"])
    p.add_argument("--note")
    p.add_argument("--by")
    return {"config": cmd_config}
