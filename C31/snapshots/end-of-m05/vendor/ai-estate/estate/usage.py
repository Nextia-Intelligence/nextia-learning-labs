"""The usage store (owner: Mei): one row per model call and per tool call, and the counters for the limits.

Every gateway replica writes here (state/usage.db, SQLite in WAL mode, so several processes can write).
A row says who called (the agent and its team), what for (capability, tool), what answered (provider,
deployment, model version), what it cost, how long it took, and how it ended. It holds no prompt and no
answer text (config/gateway.yaml prompts.keep: never), and no argument values of a tool call (a digest).

The counters (per agent and per team, per month, day and minute) are what the budgets, quotas and rate
limits read. They are shared by every replica, so three replicas do not give an agent three budgets.
"""

import json
import sqlite3
import threading
from collections import Counter
from contextlib import closing
from datetime import datetime

from estate import paths

SCHEMA = """
pragma journal_mode = wal;
create table if not exists model_calls (
  id integer primary key, ts text not null, request_id text not null, replica text, config_version text,
  agent_id text, team text, capability text, provider text, deployment text, model_version text,
  data_class text, tokens_in integer default 0, tokens_out integer default 0, cost_usd real default 0,
  gateway_ms real, upstream_ms real, recorded_ms real, status integer, outcome text not null, check_name text,
  message text, run_id text, traceparent text, fallback integer default 0, degraded integer default 0,
  guardrail text);
create index if not exists model_calls_agent on model_calls (agent_id, ts);
create table if not exists tool_calls (
  id integer primary key, ts text not null, request_id text not null, agent_id text, team text, server text,
  tool text, kind text, outcome text not null, check_name text, message text, run_id text, approver text,
  rule text, args_digest text, ms real, status integer);
create index if not exists tool_calls_agent on tool_calls (agent_id, ts);
create table if not exists counters (
  subject text not null, window text not null, cost_usd real not null default 0, tokens integer not null default 0,
  calls integer not null default 0, primary key (subject, window));
create table if not exists runs (
  agent_id text not null, run_id text not null, first_seen text not null, calls integer not null default 0,
  primary key (agent_id, run_id));
"""

MODEL_FIELDS = ("ts", "request_id", "replica", "config_version", "agent_id", "team", "capability", "provider",
                "deployment", "model_version", "data_class", "tokens_in", "tokens_out", "cost_usd", "gateway_ms",
                "upstream_ms", "recorded_ms", "status", "outcome", "check_name", "message", "run_id", "traceparent",
                "fallback", "degraded", "guardrail")
TOOL_FIELDS = ("ts", "request_id", "agent_id", "team", "server", "tool", "kind", "outcome", "check_name", "message",
               "run_id", "approver", "rule", "args_digest", "ms", "status")


class StoreDown(Exception):
    """The usage store cannot be read or written (a practice fault, or a real one)."""


def windows(ts: str) -> dict:
    t = datetime.fromisoformat(ts)
    return {"month": "m:" + t.strftime("%Y-%m"), "day": "d:" + t.strftime("%Y-%m-%d"),
            "minute": "min:" + t.strftime("%Y-%m-%dT%H:%M")}


class UsageStore:
    def __init__(self, path=None):
        self.path = path or paths.state() / "usage.db"
        self.local = threading.local()
        self.down = False          # a practice fault: the store is unreachable
        with closing(self._connect()) as con:
            con.executescript(SCHEMA)

    def _connect(self):
        con = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("pragma busy_timeout = 10000")
        return con

    def con(self):
        if self.down:
            raise StoreDown("the usage store is unreachable (practice fault)")
        c = getattr(self.local, "con", None)
        if c is None:
            c = self.local.con = self._connect()
        return c

    # --- counters -------------------------------------------------------------------------------------
    def counter(self, subject: str, window: str) -> dict:
        row = self.con().execute("select cost_usd, tokens, calls from counters where subject = ? and window = ?",
                                 (subject, window)).fetchone()
        return dict(row) if row else {"cost_usd": 0.0, "tokens": 0, "calls": 0}

    def run_calls(self, agent_id: str, run_id: str) -> int | None:
        row = self.con().execute("select calls from runs where agent_id = ? and run_id = ?", (agent_id, run_id)).fetchone()
        return None if row is None else row[0]

    # --- writes -----------------------------------------------------------------------------------------
    def record_model(self, row: dict, count_call: bool = True) -> None:
        values = [row.get(k) for k in MODEL_FIELDS]
        con = self.con()
        con.execute("begin immediate")
        try:
            con.execute(f"insert into model_calls ({', '.join(MODEL_FIELDS)}) values ({', '.join('?' * len(MODEL_FIELDS))})",
                        values)
            if count_call and row.get("agent_id") and row.get("team"):
                w = windows(row["ts"])
                tokens = int(row.get("tokens_in") or 0) + int(row.get("tokens_out") or 0)
                for subject in (row["agent_id"], f"team:{row.get('team')}"):
                    for win in w.values():
                        con.execute("insert into counters values (?, ?, ?, ?, 1) on conflict(subject, window) do update "
                                    "set cost_usd = cost_usd + excluded.cost_usd, tokens = tokens + excluded.tokens, "
                                    "calls = calls + 1", (subject, win, float(row.get("cost_usd") or 0), tokens))
                if row.get("run_id"):
                    con.execute("insert into runs values (?, ?, ?, 1) on conflict(agent_id, run_id) do update set "
                                "calls = calls + 1", (row["agent_id"], row["run_id"], row["ts"]))
            con.execute("commit")
        except Exception:
            con.execute("rollback")
            raise

    def record_tool(self, row: dict) -> None:
        self.con().execute(f"insert into tool_calls ({', '.join(TOOL_FIELDS)}) values "
                           f"({', '.join('?' * len(TOOL_FIELDS))})", [row.get(k) for k in TOOL_FIELDS])

    # --- reads for reports --------------------------------------------------------------------------------
    def rows(self, sql: str, args=()) -> list[dict]:
        return [dict(r) for r in self.con().execute(sql, args)]


def reset(path=None) -> None:
    path = path or paths.state() / "usage.db"
    for suffix in ("", "-wal", "-shm"):
        p = path.parent / (path.name + suffix)
        if p.exists():
            p.unlink()


def as_json(rows) -> str:
    return json.dumps(rows, indent=1, default=str)


# --- usage reports (python -m estate usage) ------------------------------------------------------------
GROUPS = {"agent": "agent_id", "team": "team", "capability": "capability", "model": "deployment || ' (' || "
          "coalesce(model_version, '') || ')'", "outcome": "outcome || coalesce(':' || check_name, '')",
          "replica": "replica"}


def _where(month: str | None, since: str | None) -> tuple[str, list]:
    parts, args = [], []
    if month:
        parts.append("ts like ?")
        args.append(f"{month}%")
    if since:
        parts.append("ts >= ?")
        args.append(since)
    return (" where " + " and ".join(parts)) if parts else "", args


def usage_rows(by: str = "agent", month: str | None = None, since: str | None = None, store=None) -> list[dict]:
    store = store or UsageStore()
    w, args = _where(month, since)
    return store.rows(
        f"select {GROUPS[by]} as k, count(*) as calls, sum(outcome = 'ok') as ok, sum(outcome = 'refused') as refused, "
        f"sum(outcome in ('failed', 'upstream_error')) as failed, sum(tokens_in) as tin, sum(tokens_out) as tout, "
        f"round(sum(coalesce(cost_usd, 0)), 6) as cost, sum(fallback) as fallback, sum(degraded) as degraded "
        f"from model_calls{w} group by k order by cost desc, calls desc", args)


def usage_table(by: str = "agent", month: str | None = None, since: str | None = None, store=None) -> str:
    rows = usage_rows(by, month, since, store)
    head = f"{by:<34} {'calls':>7} {'ok':>7} {'refused':>8} {'failed':>7} {'tokens in':>11} {'tokens out':>11} {'US$':>10}"
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(f"{str(r['k'] or '-'):<34} {r['calls']:>7} {r['ok'] or 0:>7} {r['refused'] or 0:>8} "
                     f"{r['failed'] or 0:>7} {r['tin'] or 0:>11,} {r['tout'] or 0:>11,} {r['cost'] or 0:>10.4f}")
    t = Counter()
    for r in rows:
        for k in ("calls", "ok", "refused", "failed", "tin", "tout"):
            t[k] += r[k] or 0
        t["cost"] += r["cost"] or 0
    lines.append(f"{'total':<34} {t['calls']:>7} {t['ok']:>7} {t['refused']:>8} {t['failed']:>7} {t['tin']:>11,} "
                 f"{t['tout']:>11,} {t['cost']:>10.4f}")
    return "\n".join(lines)


def last_rows(n: int = 1, store=None) -> str:
    """The last n rows of model calls, one field a line (empty fields left out): what the gateway keeps of a call."""
    store = store or UsageStore()
    rows = store.rows("select * from model_calls order by id desc limit ?", (n,))
    out = []
    for r in reversed(rows):
        out.append("\n".join(f"{k:<15}{v}" for k, v in r.items() if k != "id" and v not in (None, "")))
    return "\n\n".join(out) or "No model call is recorded yet."
