"""The configuration store: commands of python -m estate."""

import json
import sys

from estate.cli import actor as _actor


def cmd_config(a):
    from estate import configstore

    if a.action == "check":
        problems = configstore.validate(configstore.gather())
        print("\n".join(problems) if problems else "The configuration is valid.")
        sys.exit(1 if problems else 0)
    if a.action == "watch":
        print(json.dumps(configstore.watch(_actor(a)), indent=1))
        return
    if a.action == "status":
        s = configstore.rollout_status()
        print(f"stable version {s['stable']}" + (f" | candidate {s['candidate']} on the canary since {s['started_at']}"
                                                 if s["candidate"] else ""))
        for r in s["replicas"]:
            print(f"  replica {r['replica']:<6} runs {r['version']:<10} last seen {r['last_seen']}")
        for v in s["versions"][-5:]:
            print(f"  v{v['version']} {v['digest']} {v['created_at']} {v['created_by']}: {v['note']}")
        return
    try:
        if a.action == "publish":
            v = configstore.publish(_actor(a), a.note or "", a.stage)
            print(f"Published version {v} ({'canary replicas first' if a.stage == 'canary' else 'every replica'}).")
        elif a.action == "promote":
            print(f"Version {configstore.promote(_actor(a))} is now on every replica.")
        elif a.action == "rollback":
            print(f"Every replica is back on version {configstore.rollback(_actor(a), a.note or 'rollback')}.")
    except ValueError as e:
        sys.exit(str(e))
    ok, asked = configstore.push()
    if asked:
        print(f"Told {ok} of {asked} gateway replicas to refresh now.")


ORDER = 22


def register(sub) -> dict:
    p = sub.add_parser("config", help="publish, promote, roll back or check the configuration")
    p.add_argument("action", choices=["publish", "promote", "rollback", "status", "check", "watch"])
    p.add_argument("--stage", choices=["all", "canary"], default="all")
    p.add_argument("--note")
    p.add_argument("--by")
    return {"config": cmd_config}
