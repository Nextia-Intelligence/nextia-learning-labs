"""Which active kill switch stops a call. Both gateways ask this on every call.

The switches themselves are rows in the registry (python -m estate kill ..., estate/kill.py); they reach
every replica with the registry part of the configuration (estate/configstore.py).
"""


def blocked(snapshot: dict, agent_id: str, capability: str | None = None, tool: str | None = None,
            write: bool = False) -> str | None:
    """Which active switch stops this call (its text), or None. Used by both gateways."""
    for k in snapshot.get("kill") or []:
        s, t = k["scope"], k["target"]
        if s == "everything":
            return f"every AI call is stopped (kill switch {k['id']}: {k['reason']})"
        if s == "capability" and capability and t == capability:
            return f"the capability {capability} is stopped (kill switch {k['id']}: {k['reason']})"
        if s == "tool" and tool and t == tool:
            return f"the tool {tool} is stopped (kill switch {k['id']}: {k['reason']})"
        if s == "writes" and write and t in ("*", tool, tool.split(".")[0] if tool else ""):
            return f"writes are stopped for {t} (kill switch {k['id']}: {k['reason']})"
    return None
