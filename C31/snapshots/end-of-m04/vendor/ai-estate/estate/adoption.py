"""Adoption and friction: how far the gateway has spread, and what it refused (python -m estate adoption).

A platform that nobody moves to protects nothing, and one that refuses too much makes people go around it.
Two numbers: the share of provider calls that came through the gateway (from the provider's bill: the
gateway's key against every other key), and the share of each agent's calls that the gateway refused, and why.
"""

import csv

from estate.usage import UsageStore, _where


def adoption(month: str | None = None, bills=(), store=None) -> str:
    """The adoption report: calls through and around the gateway, and the friction per agent."""
    from estate import discovery

    store = store or UsageStore()
    lines = []
    if bills:
        inv = discovery.inventory()["keys"]
        via, direct = 0, 0
        for b in bills:
            with open(b, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if month and r["month"] != month:
                        continue
                    if (inv.get(r["key_id"]) or {}).get("status") == "gateway":
                        via += int(r["requests"])
                    else:
                        direct += int(r["requests"])
        total = via + direct
        lines.append(f"Provider calls through the gateway: {via:,} of {total:,} ({via / max(1, total):.1%}); "
                     f"around it: {direct:,}.")
    w, args = _where(month, None)
    rows = store.rows(f"select agent_id, count(*) n, sum(outcome = 'refused') refused from model_calls{w} "
                      "group by agent_id order by n desc", args)
    lines.append("Friction: the share of each agent's calls that the gateway refused.")
    for r in rows:
        why = store.rows(f"select check_name, count(*) n from model_calls{w} {'and' if w else 'where'} agent_id is ? "
                         "and outcome = 'refused' group by check_name order by n desc", [*args, r["agent_id"]])
        lines.append(f"  {str(r['agent_id'] or 'unknown'):<20} {r['refused'] or 0:>6} of {r['n']:>6} refused "
                     f"({(r['refused'] or 0) / max(1, r['n']):.1%})" +
                     (": " + ", ".join(f"{x['check_name']} {x['n']}" for x in why) if why else ""))
    return "\n".join(lines)
