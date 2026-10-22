"""The configuration store: what every gateway replica must know, in versions, rolled out in stages.

A gateway replica never reads the registry or the YAML files itself. It asks the control plane for a
SNAPSHOT (GET /v1/config) and keeps the last good one in memory, so a control-plane outage does not stop
calls (up to the cache's limit, config/gateway.yaml). A snapshot has two parts:

- the published configuration (catalog, providers, models, gateway settings, approval policy, teams, tools):
  it changes only when someone publishes a new version, and a new version can go to the canary replicas
  first (`python -m estate config publish --stage canary`), then to all (`promote`), or back (`rollback`);
- the registry part (registrations, credentials revoked, kill switches): it is always the latest, because a
  suspension or a kill switch must reach every replica at once.
"""

import hashlib
import json
import os
import urllib.request
from contextlib import closing
from datetime import datetime

import yaml

from estate import catalog, clock, paths, registry

SCHEMA = """
create table if not exists config_versions (
  version integer primary key, content text not null, digest text not null, created_at text not null,
  created_by text not null, note text not null);
create table if not exists rollout (
  replica text primary key, version integer not null, assigned_at text not null);
create table if not exists rollout_state (
  id integer primary key check (id = 1), stable integer, candidate integer, stage text, started_at text);
create table if not exists replicas (
  replica text primary key, url text, version text, last_seen text);
insert or ignore into rollout_state (id, stable, candidate, stage, started_at) values (1, null, null, null, null);
"""


def db():
    con = registry.db()
    con.executescript(SCHEMA)
    return con


def gather(folder=None) -> dict:
    """The published part, read from the YAML files in config/ (validated before publish)."""
    folder = folder or paths.CONFIG

    def y(name, part=None, default=None):
        """A file of config/ (a later module adds some of them: then the default)."""
        path = folder / name
        if not path.exists():
            return default
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data[part] if part else data

    return {
        "catalog": y("catalog.yaml"), "models": y("models.yaml", "models"), "providers": y("providers.yaml", "providers"),
        "settings": y("gateway.yaml", default={}), "data_classes": y("data-classes.yaml", "classes"),
        "teams": y("teams.yaml", "teams"), "people": y("people.yaml", "people"),
        "policy": y("policy/approvals.yaml", default=None), "tools": y("tools.yaml", default={"servers": {}}),
    }


def validate(content: dict) -> list[str]:
    problems = catalog.check(content["catalog"], content["models"], content["providers"])
    if content.get("policy"):     # the approval policy arrives with the tool gateway (a later module)
        from estate import policy

        problems += policy.check_policy(content["policy"])
    for mode in (content["settings"].get("failure_modes") or {}).values():
        if mode not in ("fail_open", "fail_closed"):
            problems.append(f"failure mode {mode}: fail_open or fail_closed")
    return problems


def publish(actor: str, note: str, stage: str = "all", content: dict | None = None, force: bool = False) -> int:
    """A new version of the published configuration. stage "all": every replica gets it now; "canary": only the
    canary replicas (config/gateway.yaml rollout.canary), until promote or rollback."""
    content = content or gather()
    problems = validate(content)
    if problems and not force:
        raise ValueError("The configuration has problems; nothing was published:\n  " + "\n  ".join(problems))
    text = json.dumps(content, sort_keys=True, default=str)
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    with closing(db()) as con, con:
        v = (con.execute("select max(version) from config_versions").fetchone()[0] or 0) + 1
        con.execute("insert into config_versions values (?, ?, ?, ?, ?, ?)", (v, text, digest, clock.iso(), actor, note))
        state = con.execute("select * from rollout_state").fetchone()
        if stage == "all" or state["stable"] is None:
            con.execute("update rollout_state set stable = ?, candidate = null, stage = null, started_at = null", (v,))
            con.execute("delete from rollout")
        else:
            canary = content["settings"].get("rollout", {}).get("canary") or ["a"]
            con.execute("update rollout_state set candidate = ?, stage = 'canary', started_at = ?", (v, clock.iso()))
            con.execute("delete from rollout")
            for r in canary:
                con.execute("insert into rollout values (?, ?, ?)", (r, v, clock.iso()))
        registry.event(con, None, "config_published", actor, version=v, stage=stage, note=note, digest=digest)
        registry.bump(con)
    return v


def promote(actor: str) -> int:
    with closing(db()) as con, con:
        s = con.execute("select * from rollout_state").fetchone()
        if not s["candidate"]:
            raise ValueError("No staged version to promote.")
        con.execute("update rollout_state set stable = candidate, candidate = null, stage = null, started_at = null")
        con.execute("delete from rollout")
        registry.event(con, None, "config_promoted", actor, version=s["candidate"])
        registry.bump(con)
        return s["candidate"]


def rollback(actor: str, reason: str) -> int:
    """Every replica back to the stable version (during a canary), or to the version before it."""
    with closing(db()) as con, con:
        s = con.execute("select * from rollout_state").fetchone()
        if s["candidate"]:
            back = s["stable"]
            con.execute("update rollout_state set candidate = null, stage = null, started_at = null")
        else:
            back = con.execute("select max(version) from config_versions where version < ?",
                               (s["stable"],)).fetchone()[0]
            if back is None:
                raise ValueError("There is no earlier version.")
            con.execute("update rollout_state set stable = ?", (back,))
        con.execute("delete from rollout")
        registry.event(con, None, "config_rolled_back", actor, to=back, reason=reason)
        registry.bump(con)
        return back


def version_for(replica: str) -> int | None:
    with closing(db()) as con:
        row = con.execute("select version from rollout where replica = ?", (replica,)).fetchone()
        if row:
            return row[0]
        return con.execute("select stable from rollout_state").fetchone()[0]


def rollout_status() -> dict:
    with closing(db()) as con:
        s = dict(con.execute("select * from rollout_state").fetchone())
        s["replicas"] = [dict(r) for r in con.execute("select * from replicas order by replica")]
        s["versions"] = [dict(r) for r in con.execute(
            "select version, digest, created_at, created_by, note from config_versions order by version")]
    return s


def registry_part() -> dict:
    """The part that is always the latest: registrations, revoked credentials, kill switches."""
    from estate import identity

    agents = {}
    for reg in registry.all_registrations():
        f = reg.form
        agents[reg.agent_id] = {
            "status": reg.status, "team": f["team"], "kind": f["kind"], "owner": f["owner"],
            "risk_tier": f["risk_tier"], "data_classes": f.get("data_classes") or [],
            "capabilities": f.get("capabilities") or [], "tools": f.get("tools") or [], "autonomy": f["autonomy"],
            "budget_usd_month": f.get("budget_usd_month") or 0, "limits": f.get("limits") or {},
            "pins": f.get("pins") or {}, "revoked_before": identity.revoked_before(reg.agent_id),
            "failure_mode": (f.get("long_form") or {}).get("failure_mode"),
        }
    with closing(db()) as con:
        kills = [dict(r) for r in con.execute(
            "select id, scope, target, created_at, created_by, reason from kill_switches where lifted_at is null")]
        rev = con.execute("select n from revision").fetchone()[0]
    return {"revision": rev, "agents": agents, "kill": kills}


def snapshot(replica: str = "a") -> dict:
    """What a replica gets from GET /v1/config: the published version assigned to it, and the registry part."""
    v = version_for(replica)
    if v is None:
        raise LookupError("Nothing is published yet: run python -m estate config publish")
    with closing(db()) as con:
        row = con.execute("select content, digest from config_versions where version = ?", (v,)).fetchone()
    from estate import identity

    reg = registry_part()
    return {"version": f"v{v}.r{reg['revision']}", "config_version": v, "digest": row["digest"],
            "created_at": clock.iso(), **json.loads(row["content"]), **reg, "jwks": identity.jwks()}


def seen(replica: str, url: str, version: str) -> None:
    with closing(db()) as con, con:
        con.execute("insert into replicas values (?, ?, ?, ?) on conflict(replica) do update set url = excluded.url, "
                    "version = excluded.version, last_seen = excluded.last_seen", (replica, url, version, clock.iso()))


def replica_urls() -> list[str]:
    with closing(db()) as con:
        return [r[0] for r in con.execute("select url from replicas where url is not null and url != ''")]


def age_seconds(iso: str) -> float:
    return (clock.now() - datetime.fromisoformat(iso)).total_seconds()


def push(extra_urls: list[str] | None = None, timeout: float = 2.0) -> tuple[int, int]:
    """Ask every known replica (and the tool gateway) to fetch the configuration now. Returns (answered, asked)."""
    if os.environ.get("ESTATE_PUSH", "on") == "off":   # a practice switch: wait for the replicas' own polls
        return 0, 0
    urls = replica_urls() + list(extra_urls or [])
    ok = 0
    for url in urls:
        try:
            req = urllib.request.Request(url.rstrip("/") + "/admin/refresh", data=b"{}", method="POST",
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                json.loads(r.read())
                ok += 1
        except OSError:
            pass
    return ok, len(urls)


ERRORS = ("guardrail", "provider", "route", "capability", "data_class")


def watch(actor: str = "usr-kwame", store=None) -> dict:
    """The canary's verdict: once the canary replicas have served `watch_requests` calls with the candidate
    version, promote it if their error rate is at most `max_error_rate`, else roll back. An "error" is a call that
    the configuration can break: refused by a guardrail, a capability or data-class check, or failed at routing or
    at the provider. Refusals by limits or identity are the agents' doing, not the configuration's."""
    from estate.usage import UsageStore

    s = rollout_status()
    if not s["candidate"]:
        return {"state": "nothing staged"}
    content = json.loads(_content(s["candidate"]))
    roll = content["settings"].get("rollout") or {}
    canary = roll.get("canary") or ["a"]
    need, limit = int(roll.get("watch_requests", 40)), float(roll.get("max_error_rate", 0.05))
    store = store or UsageStore()
    marks = ",".join("?" * len(canary))
    rows = store.rows(f"select outcome, check_name from model_calls where replica in ({marks}) and config_version like ?",
                      [*canary, f"v{s['candidate']}.%"])
    errors = sum(1 for r in rows if r["outcome"] != "ok" and (r["check_name"] in ERRORS))
    out = {"candidate": s["candidate"], "canary": canary, "seen": len(rows), "errors": errors,
           "error_rate": round(errors / len(rows), 4) if rows else None}
    if len(rows) < need and errors / need <= limit:
        out["state"] = f"watching ({len(rows)} of {need} requests)"
    elif errors / max(len(rows), 1) > limit:
        out["state"] = f"rolled back to v{rollback(actor, f'canary error rate {errors}/{len(rows)}')}"
    else:
        out["state"] = f"promoted v{promote(actor)}"
    return out


def _content(version: int) -> str:
    with closing(db()) as con:
        return con.execute("select content from config_versions where version = ?", (version,)).fetchone()[0]
