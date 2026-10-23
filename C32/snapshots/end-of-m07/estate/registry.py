"""The registry: every agent and app that may call a model or a tool, with its owner, risk and limits.

A registration starts as a form (registrations/<id>.yaml). `register()` checks the form against the
catalog, the data classes, the teams and the people, and stores it in SQLite (state/registry.db) with its
lifecycle: pending (high risk, until a review), active, suspended, draining, retired. Every change is an
event with who did it and why: the registry is also the audit trail of the estate's AI.
"""

import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from datetime import date, timedelta

import yaml

from estate import clock, paths

RISK_TIERS = ("low", "medium", "high")
AUTONOMY = ("suggests", "acts-with-approval", "acts")
KINDS = ("app", "agent", "tool-server", "script")
STATUSES = ("pending", "active", "suspended", "draining", "retired")
SHORT_FORM = ("id", "name", "kind", "owner", "team", "purpose", "users", "risk_tier", "data_classes",
              "capabilities", "tools", "autonomy", "budget_usd_month", "limits", "review_date")
LONG_FORM = ("impact", "human_oversight", "failure_mode", "incident_contact", "data_retention")
LIMITS = ("requests_per_minute", "tokens_per_day", "max_calls_per_run")
REVIEW_MONTHS = {"low": 12, "medium": 6, "high": 3}   # the longest time until the next review, by risk tier
ID = re.compile(r"^[a-z][a-z0-9-]{2,40}$")
TOOL = re.compile(r"^[a-z][a-z0-9_-]*\.[a-z][a-z0-9_]*$")

SCHEMA = """
create table if not exists agents (
  agent_id text primary key, form text not null, status text not null, version integer not null,
  created_at text not null, updated_at text not null);
create table if not exists events (
  id integer primary key, at text not null, agent_id text, action text not null, actor text not null,
  detail text not null);
create table if not exists credentials (
  credential_id text primary key, client_id text not null, agent_id text not null, secret_hash text not null,
  created_at text not null, revoked_at text);
create table if not exists revocations (
  id integer primary key, credential_id text not null, agent_id text not null, at text not null,
  actor text not null, reason text not null);
create table if not exists kill_switches (
  id integer primary key, scope text not null, target text not null, created_at text not null,
  created_by text not null, reason text not null, lifted_at text);
create table if not exists exceptions (
  id integer primary key, agent_id text not null, rule text not null, reason text not null,
  approved_by text not null, until text not null, created_at text not null);
create table if not exists incidents (
  id integer primary key, kind text not null, started_at text not null, ended_at text, summary text not null,
  agents text not null default '[]');
create table if not exists revision (id integer primary key check (id = 1), n integer not null);
insert or ignore into revision (id, n) values (1, 0);
"""


class FormError(ValueError):
    """The registration form has problems: `problems` lists every one."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def now() -> str:
    return clock.iso()


def load_yaml(name: str) -> dict:
    return yaml.safe_load((paths.CONFIG / name).read_text(encoding="utf-8")) or {}


def people() -> dict:
    return load_yaml("people.yaml")["people"]


def teams() -> dict:
    return load_yaml("teams.yaml")["teams"]


def data_classes() -> dict:
    return load_yaml("data-classes.yaml")["classes"]


@dataclass
class Registration:
    agent_id: str
    form: dict
    status: str
    version: int
    created_at: str = ""
    updated_at: str = ""
    credentials: list[dict] = field(default_factory=list)

    def __getattr__(self, name):
        try:
            return self.__dict__["form"][name]
        except KeyError:
            raise AttributeError(name) from None

    @property
    def limits(self) -> dict:
        return self.form.get("limits") or {}


def db(path=None) -> sqlite3.Connection:
    con = sqlite3.connect(path or paths.state() / "registry.db", timeout=10)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def bump(con) -> int:
    """Every change to the registry raises its revision: the gateways see a new configuration."""
    con.execute("update revision set n = n + 1 where id = 1")
    return con.execute("select n from revision").fetchone()[0]


def revision() -> int:
    with closing(db()) as con:
        return con.execute("select n from revision").fetchone()[0]


def event(con, agent_id: str | None, action: str, actor: str, **detail) -> None:
    con.execute("insert into events (at, agent_id, action, actor, detail) values (?, ?, ?, ?, ?)",
                (now(), agent_id, action, actor, json.dumps(detail, ensure_ascii=False, sort_keys=True)))


def check_form(form: dict, catalog: dict | None = None, today: date | None = None) -> list[str]:
    """Every problem with a registration form, in plain words (empty list: the form is complete)."""
    from estate.catalog import load_catalog

    catalog = catalog or load_catalog()
    today = today or clock.now().date()
    p = []
    missing = [k for k in SHORT_FORM if k not in form or form[k] in (None, "")]
    if missing:
        p.append(f"missing: {', '.join(missing)}")
    if form.get("id") and not ID.match(str(form["id"])):
        p.append("id: lower-case letters, digits and hyphens, 3 to 41 characters")
    if form.get("kind") and form["kind"] not in KINDS:
        p.append(f"kind: one of {', '.join(KINDS)}")
    who = people()
    owner = who.get(form.get("owner"))
    if form.get("owner") and owner is None:
        p.append(f"owner {form['owner']}: not a person in config/people.yaml")
    elif owner and owner.get("left"):
        p.append(f"owner {form['owner']}: left the company on {owner['left']}; a registration needs an owner who is here")
    if form.get("team") and form["team"] not in teams():
        p.append(f"team {form['team']}: not a team in config/teams.yaml")
    tier = form.get("risk_tier")
    if tier and tier not in RISK_TIERS:
        p.append(f"risk_tier: one of {', '.join(RISK_TIERS)}")
    classes = data_classes()
    for c in form.get("data_classes") or []:
        if c not in classes:
            p.append(f"data class {c}: not in config/data-classes.yaml")
        elif classes[c].get("never_to_a_model") and form.get("capabilities"):
            p.append(f"data class {c}: never sent to a model, so an agent with capabilities cannot register it")
        elif classes[c].get("never_to_a_model"):
            # A tool server lists no capabilities, but its answers go into an agent's context, and from there
            # to a model: the same rule applies (a gap found by the case study on public MCP servers).
            p.append(f"data class {c}: never sent to a model, and a tool's answer goes to the agent's model, "
                     "so a tool server cannot register it")
    caps = catalog["capabilities"]
    for c in form.get("capabilities") or []:
        if c not in caps:
            p.append(f"capability {c}: not in the catalog")
            continue
        allowed = set(caps[c]["contract"].get("data_classes") or [])
        for dc in form.get("data_classes") or []:
            if dc in classes and dc not in allowed:
                p.append(f"capability {c} does not allow the data class {dc}")
    for t in form.get("tools") or []:
        if not TOOL.match(str(t)):
            p.append(f"tool {t}: write it as server.tool, for example orders.get_order")
    if form.get("autonomy") and form["autonomy"] not in AUTONOMY:
        p.append(f"autonomy: one of {', '.join(AUTONOMY)}")
    if tier == "high" and form.get("autonomy") == "acts":
        p.append("a high-risk agent may not act without a person's approval (autonomy: acts-with-approval)")
    budget = form.get("budget_usd_month")
    if budget is not None and (not isinstance(budget, (int, float)) or budget < 0):
        p.append("budget_usd_month: a number, 0 or more")
    limits = form.get("limits") or {}
    for k in LIMITS:
        if k not in limits or not isinstance(limits[k], int) or limits[k] < 0:
            p.append(f"limits.{k}: a whole number, 0 or more")
    if form.get("review_date"):
        try:
            due = date.fromisoformat(str(form["review_date"]))
            months = REVIEW_MONTHS.get(tier or "low", 12)
            if due > today + timedelta(days=31 * months):
                p.append(f"review_date: a {tier} risk registration is reviewed at least every {months} months")
        except ValueError:
            p.append("review_date: a date, for example 2027-01-15")
    if tier == "high":
        lf = form.get("long_form") or {}
        gaps = [k for k in LONG_FORM if not lf.get(k)]
        if gaps:
            p.append(f"high risk needs the long form: missing long_form.{', long_form.'.join(gaps)}")
    return p


def read_form(path) -> dict:
    form = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    if isinstance(form.get("review_date"), date):
        form["review_date"] = form["review_date"].isoformat()
    lf = form.get("long_form") or {}
    for k, v in list(lf.items()):
        if isinstance(v, date):
            lf[k] = v.isoformat()
    return form


def register(form: dict, actor: str, today: date | None = None) -> Registration:
    """Store a new registration (or a new version of a changed one). High risk waits for a review."""
    problems = check_form(form, today=today)
    if problems:
        raise FormError(problems)
    with closing(db()) as con, con:
        old = con.execute("select * from agents where agent_id = ?", (form["id"],)).fetchone()
        t = now()
        if old is None:
            status = "pending" if form["risk_tier"] == "high" else "active"
            con.execute("insert into agents values (?, ?, ?, 1, ?, ?)",
                        (form["id"], json.dumps(form, sort_keys=True), status, t, t))
            event(con, form["id"], "register", actor, status=status, version=1)
        else:
            if old["status"] == "retired":
                raise FormError([f"{form['id']} is retired: a retired ID is never used again; choose a new ID"])
            before = json.loads(old["form"])
            changed = sorted(k for k in set(before) | set(form) if before.get(k) != form.get(k))
            # A high-risk agent that changes what it may do needs a new review before it acts again.
            review = form["risk_tier"] == "high" and any(
                k in changed for k in ("capabilities", "tools", "data_classes", "autonomy", "risk_tier", "limits"))
            status = "pending" if review else old["status"]
            con.execute("update agents set form = ?, status = ?, version = version + 1, updated_at = ? where "
                        "agent_id = ?", (json.dumps(form, sort_keys=True), status, t, form["id"]))
            event(con, form["id"], "change", actor, changed=changed, status=status, version=old["version"] + 1)
        bump(con)
    return get(form["id"])


def get(agent_id: str) -> Registration | None:
    with closing(db()) as con:
        row = con.execute("select * from agents where agent_id = ?", (agent_id,)).fetchone()
        if row is None:
            return None
        creds = [dict(r) for r in con.execute(
            "select credential_id, client_id, created_at, revoked_at from credentials where agent_id = ? "
            "order by rowid",
            (agent_id,))]
    return Registration(row["agent_id"], json.loads(row["form"]), row["status"], row["version"], row["created_at"],
                        row["updated_at"], creds)


def all_registrations() -> list[Registration]:
    with closing(db()) as con:
        ids = [r[0] for r in con.execute("select agent_id from agents order by agent_id")]
    return [get(i) for i in ids]


def set_status(agent_id: str, status: str, actor: str, reason: str) -> Registration:
    if status not in STATUSES:
        raise ValueError(f"status: one of {', '.join(STATUSES)}")
    reg = get(agent_id)
    if reg is None:
        raise KeyError(f"No registration {agent_id}.")
    if reg.status == "retired":
        raise ValueError(f"{agent_id} is retired: it cannot change any more.")
    if not reason.strip():
        raise ValueError("Give a reason: it goes into the audit trail.")
    with closing(db()) as con, con:
        con.execute("update agents set status = ?, updated_at = ? where agent_id = ?", (status, now(), agent_id))
        event(con, agent_id, status, actor, reason=reason, before=reg.status)
        if status == "retired":   # a retired agent keeps no working credential
            revoke_credentials(con, agent_id, actor, "retired")
        bump(con)
    return get(agent_id)


def revoke_credentials(con, agent_id: str, actor: str, reason: str) -> list[str]:
    """Revoke every live credential of an agent, inside the caller's transaction. Each revocation is also kept in
    its own table, which nothing ever updates or deletes: a credential that was revoked stays revoked, even when
    the agent gets new credentials later. Returns the revoked credential IDs."""
    ids = [r[0] for r in con.execute(
        "select credential_id from credentials where agent_id = ? and revoked_at is null order by rowid", (agent_id,))]
    t = now()
    for cid in ids:
        con.execute("update credentials set revoked_at = ? where credential_id = ?", (t, cid))
        con.execute("insert into revocations (credential_id, agent_id, at, actor, reason) values (?, ?, ?, ?, ?)",
                    (cid, agent_id, t, actor, reason))
    event(con, agent_id, "credentials_revoked", actor, reason=reason, credentials=ids)
    return ids


def review(agent_id: str, actor: str, next_review: str, approve: bool = True, note: str = "") -> Registration:
    """A review: the platform owner (or the agent's reviewer) checks the registration and sets the next date."""
    reg = get(agent_id)
    if reg is None:
        raise KeyError(f"No registration {agent_id}.")
    form = dict(reg.form, review_date=next_review)
    problems = check_form(form)
    if problems:
        raise FormError(problems)
    with closing(db()) as con, con:
        status = ("active" if approve and reg.status == "pending" else
                  reg.status if approve else "suspended")
        con.execute("update agents set form = ?, status = ?, updated_at = ? where agent_id = ?",
                    (json.dumps(form, sort_keys=True), status, now(), agent_id))
        event(con, agent_id, "review", actor, approved=approve, next_review=next_review, note=note, status=status)
        bump(con)
    return get(agent_id)


def review_due(today: date | None = None, within_days: int = 30) -> list[tuple[Registration, str]]:
    """Registrations that need attention: a review that is overdue or near, an owner who left, a pin that retires."""
    today = today or clock.now().date()
    who = people()
    out = []
    for reg in all_registrations():
        if reg.status == "retired":
            continue
        due = date.fromisoformat(reg.form["review_date"])
        if due < today:
            out.append((reg, f"review overdue since {due} ({(today - due).days} days)"))
        elif due <= today + timedelta(days=within_days):
            out.append((reg, f"review due on {due}"))
        owner = who.get(reg.form["owner"], {})
        if owner.get("left"):
            out.append((reg, f"owner {reg.form['owner']} left on {owner['left']}: find a new owner or retire it"))
        for cap, pin in (reg.form.get("pins") or {}).items():
            retire = date.fromisoformat(str(pin["retire_by"]))
            if retire <= today + timedelta(days=60):
                out.append((reg, f"pin {cap} -> {pin['deployment']} ({pin.get('model_version', '')}) retires on {retire}"))
    return out


def events(agent_id: str | None = None, limit: int = 200) -> list[dict]:
    with closing(db()) as con:
        q = "select * from events" + (" where agent_id = ?" if agent_id else "") + " order by id desc limit ?"
        rows = con.execute(q, ((agent_id, limit) if agent_id else (limit,))).fetchall()
    return [dict(r, detail=json.loads(r["detail"])) for r in rows]
