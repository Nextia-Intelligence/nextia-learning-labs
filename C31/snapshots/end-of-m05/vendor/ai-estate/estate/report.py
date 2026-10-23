"""The evidence that governance asks for, from the registry and the usage store.

    python -m estate report --month 2026-09 [--out report.md]

The gateway's records say who called which capability, which model answered, what it cost and how it ended.
They do not say whether an answer was right, or what a whole task cost: for that, join them with the app's
traces (the observability course) by the run ID and the traceparent that every call carries.
"""

import json
from collections import Counter
from contextlib import closing

from estate import registry
from estate.usage import UsageStore, _where, usage_rows

def _incidents_and_exceptions(month: str):
    with closing(registry.db()) as con:
        inc = [dict(r) for r in con.execute("select * from incidents where started_at like ? order by started_at",
                                            (f"{month}%",))]
        exc = [dict(r) for r in con.execute("select * from exceptions order by created_at")]
    return inc, exc


def monthly(month: str, store=None, discovery_file=None) -> str:
    """The month's estate report, in Markdown: what the governance board reads."""
    from estate import paths

    store = store or UsageStore()
    regs = registry.all_registrations()
    teams = registry.teams()
    by_agent = {r["k"]: r for r in usage_rows("agent", month, store=store)}
    by_team = {r["k"]: r for r in usage_rows("team", month, store=store)}
    lines = [f"# Larkfield AI estate report: {month}", "",
             "Made by `python -m estate report` from the registry and the gateways' usage records. Every number "
             "names its source; nothing here says whether an answer was right (see the evaluations).", ""]
    # 1. Inventory.
    status = Counter(r.status for r in regs)
    lines += ["## 1. Inventory", "", f"{len(regs)} registrations: " + ", ".join(f"{n} {s}" for s, n in sorted(status.items())),
              "", "| Agent or app | Kind | Owner | Team | Risk | Status | Review by |", "|---|---|---|---|---|---|---|"]
    for r in regs:
        f = r.form
        lines.append(f"| {r.agent_id} | {f['kind']} | {f['owner']} | {f['team']} | {f['risk_tier']} | {r.status} | "
                     f"{f['review_date']} |")
    found = []
    dpath = discovery_file or paths.state() / "discovery.json"
    if dpath.exists():
        found = json.loads(dpath.read_text())
    if found:
        lines += ["", f"Found outside the registry ({len(found)} findings, `python -m estate discover`):", ""]
        lines += [f"- {f['evidence']}: {f['finding']}" for f in found[:12]]
    calls_registered = sum((by_agent.get(r.agent_id) or {}).get("ok") or 0 for r in regs)
    lines += ["", f"Model calls through the gateway this month: {calls_registered:,} answered for registered agents.", ""]
    # 2. Risk.
    tiers = Counter(r.form["risk_tier"] for r in regs if r.status != "retired")
    lines += ["## 2. Risk tiers", "", ", ".join(f"{tiers.get(t, 0)} {t}" for t in ("high", "medium", "low")) + " (not retired).", ""]
    for r in regs:
        if r.form["risk_tier"] == "high" and r.status != "retired":
            lf = r.form.get("long_form") or {}
            lines.append(f"- {r.agent_id}: failure mode {lf.get('failure_mode')}, kill switch tested: "
                         f"{lf.get('kill_switch_tested') or 'not yet'}")
    # 3. Spending.
    lines += ["", "## 3. Spending (US$, from the gateways' records and the dated prices)", "",
              "| Agent | Team | Calls answered | Refused | Cost | Budget | Used |", "|---|---|---|---|---|---|---|"]
    for r in regs:
        u = by_agent.get(r.agent_id) or {}
        b = float(r.form.get("budget_usd_month") or 0)
        cost = u.get("cost") or 0.0
        lines.append(f"| {r.agent_id} | {r.form['team']} | {u.get('ok') or 0:,} | {u.get('refused') or 0:,} | "
                     f"{cost:.2f} | {b:.2f} | {cost / b:.0%} |" if b else
                     f"| {r.agent_id} | {r.form['team']} | {u.get('ok') or 0:,} | {u.get('refused') or 0:,} | "
                     f"{cost:.2f} | - | - |")
    lines += ["", "| Team | Cost | Budget |", "|---|---|---|"]
    for t, cfg in teams.items():
        lines.append(f"| {t} | {(by_team.get(t) or {}).get('cost') or 0:.2f} | {cfg['budget_usd_month']:.2f} |")
    lines += ["", "| Capability | Calls answered | Cost |", "|---|---|---|"]
    for r in usage_rows("capability", month, store=store):
        if r["k"]:
            lines.append(f"| {r['k']} | {r['ok'] or 0:,} | {r['cost'] or 0:.2f} |")
    lines += ["", "| Model that answered | Calls |", "|---|---|"]
    for r in usage_rows("model", month, store=store):
        if r["k"] and r["ok"]:
            lines.append(f"| {r['k']} | {r['ok']:,} |")
    # 4. Controls.
    w, args = _where(month, None)
    checks = store.rows(f"select check_name, count(*) n from model_calls{w} {'and' if w else 'where'} outcome != 'ok' "
                        "group by check_name order by n desc", args)
    lines += ["", "## 4. What the controls stopped", "", "| Check | Model calls stopped or failed |", "|---|---|"]
    lines += [f"| {c['check_name'] or '-'} | {c['n']:,} |" for c in checks] or ["| none | 0 |"]
    extra = store.rows(f"select sum(fallback) fb, sum(degraded) dg, sum(guardrail is not null) gr from model_calls{w}", args)[0]
    lines += ["", f"Answers from a fallback: {extra['fb'] or 0:,}. Calls served in fail-open mode: {extra['dg'] or 0:,}. "
                  f"Calls changed by a guardrail: {extra['gr'] or 0:,}.", ""]
    tools = store.rows(f"select agent_id, kind, outcome, count(*) n, count(approver) approved from tool_calls{w} "
                       "group by agent_id, kind, outcome order by agent_id, kind", args)
    if tools:
        lines += ["| Agent | Tool calls | Outcome | Calls | With an approval |", "|---|---|---|---|---|"]
        lines += [f"| {t['agent_id'] or '-'} | {t['kind'] or '-'} | {t['outcome']} | {t['n']:,} | {t['approved']:,} |"
                  for t in tools]
    # 5. Exceptions and incidents.
    inc, exc = _incidents_and_exceptions(month)
    lines += ["", "## 5. Exceptions and incidents", ""]
    lines += [f"- Exception {e['id']}: {e['agent_id']} may skip {e['rule']} until {e['until']} ({e['reason']}; "
              f"approved by {e['approved_by']})" for e in exc] or ["- No exceptions."]
    lines += [f"- Incident {i['id']} ({i['kind']}), {i['started_at'][:16]} to {(i['ended_at'] or 'open')[:16]}: "
              f"{i['summary']}" for i in inc] or ["- No incidents."]
    due = registry.review_due()
    lines += ["", "## 6. Reviews and owners", ""]
    lines += [f"- {r.agent_id}: {why}" for r, why in due] or ["- Nothing due."]
    lines += ["", "## 7. What this evidence cannot answer", "",
              "- Whether the answers were right: that is each consumer's evaluation (the remap gate) and its reviews.",
              "- What a whole task cost or why it failed: join these records with the app's traces by run ID.",
              "- AI inside bought tools, and AI used outside Larkfield's network: the buying process and asking people.",
              ""]
    return "\n".join(lines)
