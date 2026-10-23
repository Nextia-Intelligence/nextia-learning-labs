"""The remap gate: commands of python -m estate."""

import json



def cmd_remap(a):
    from estate import remap

    provider, _, deployment = a.to.partition("/")
    params = dict(p.split("=", 1) for p in a.param or [])
    result = remap.gate(a.capability, provider, deployment, params, consumers_only=a.consumer or None,
                        also=a.also)
    print(remap.render(result))
    if a.save:
        open(a.save, "w").write(json.dumps(result, indent=1))


ORDER = 11


def register(sub) -> dict:
    p = sub.add_parser("remap", help="run the remap gate: every consumer's evaluation on a candidate model")
    p.add_argument("action", choices=["gate"])
    p.add_argument("capability")
    p.add_argument("--to", required=True, help="provider/deployment, for example azure/chat-small")
    p.add_argument("--param", action="append", help="a setting for the new model, for example reasoning_effort=none")
    p.add_argument("--consumer", action="append")
    p.add_argument("--also", action="append", help="a what-if registration form to add (constructed)")
    p.add_argument("--save")
    return {"remap": cmd_remap}
