"""Kill switches and containment: from "watch it" to "stop everything", in levels.

    level 1  throttle    lower one agent's rate limit (python -m estate register with new limits)
    level 2  writes      stop the writes of one tool, or of every tool (reads go on)
    level 3  capability  stop one capability for every agent (for example after a bad model change)
    level 4  agent       suspend one agent (model and tool calls refused); drain: finish running work first
    level 5  credentials revoke the agent's credentials (its tokens die too)
    level 6  everything  stop every model and tool call of the estate

A switch is a row in the registry (kill_switches); it reaches every replica with the registry part of the
configuration. Because the replicas would otherwise see it only at their next poll, the command also tells
every replica it knows to refresh now (configstore.push), and prints how many answered.
"""

from contextlib import closing

from estate import clock, registry

SCOPES = ("writes", "tool", "capability", "everything")


def add(scope: str, target: str, actor: str, reason: str) -> int:
    if scope not in SCOPES:
        raise ValueError(f"scope: one of {', '.join(SCOPES)}")
    if not reason.strip():
        raise ValueError("Give a reason: it goes into the audit trail and the incident report.")
    with closing(registry.db()) as con, con:
        cur = con.execute("insert into kill_switches (scope, target, created_at, created_by, reason) values "
                          "(?, ?, ?, ?, ?)", (scope, target, clock.iso(), actor, reason))
        registry.event(con, None, "kill_switch", actor, scope=scope, target=target, reason=reason, id=cur.lastrowid)
        registry.bump(con)
        return cur.lastrowid


def lift(switch_id: int, actor: str, reason: str) -> None:
    with closing(registry.db()) as con, con:
        n = con.execute("update kill_switches set lifted_at = ? where id = ? and lifted_at is null",
                        (clock.iso(), switch_id)).rowcount
        if not n:
            raise KeyError(f"No active kill switch {switch_id}.")
        registry.event(con, None, "kill_switch_lifted", actor, id=switch_id, reason=reason)
        registry.bump(con)


def active() -> list[dict]:
    with closing(registry.db()) as con:
        return [dict(r) for r in con.execute("select * from kill_switches where lifted_at is null order by id")]
