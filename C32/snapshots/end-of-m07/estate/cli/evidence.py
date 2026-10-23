"""Usage and evidence: commands of python -m estate."""

import json
import sys

from estate import paths
from estate.cli import actor as _actor


def cmd_report(a):
    from estate import report

    text = report.monthly(a.month)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"Saved the report to {a.out}")
    else:
        print(text)


def cmd_discover(a):
    from estate import discovery

    findings = discovery.discover(a.bill, a.egress, a.scan)
    print(discovery.render(findings))
    (paths.state() / "discovery.json").write_text(json.dumps(findings, indent=1))


def cmd_incident(a):
    from contextlib import closing

    from estate import clock, registry

    with closing(registry.db()) as con, con:
        if a.action == "add":
            cur = con.execute("insert into incidents (kind, started_at, summary, agents) values (?, ?, ?, ?)",
                              (a.kind, a.at or clock.iso(), a.summary, json.dumps(a.agent or [])))
            registry.event(con, None, "incident", _actor(a), id=cur.lastrowid, kind=a.kind, summary=a.summary)
            print(f"Incident {cur.lastrowid} opened.")
        elif a.action == "end":
            con.execute("update incidents set ended_at = ? where id = ?", (a.at or clock.iso(), int(a.id)))
            print(f"Incident {a.id} ended.")
        else:
            for r in con.execute("select * from incidents order by id"):
                print(f"{r['id']:>3} {r['kind']:<12} {r['started_at']} -> {r['ended_at'] or 'open'}: {r['summary']}")


def cmd_exception(a):
    from contextlib import closing

    from estate import clock, registry

    with closing(registry.db()) as con, con:
        if a.action == "add":
            if not a.reason or not a.until:
                sys.exit("An exception needs --reason and --until (a date): exceptions end.")
            cur = con.execute("insert into exceptions (agent_id, rule, reason, approved_by, until, created_at) values "
                              "(?, ?, ?, ?, ?, ?)", (a.agent, a.rule, a.reason, _actor(a), a.until, clock.iso()))
            registry.event(con, a.agent, "exception", _actor(a), id=cur.lastrowid, rule=a.rule, until=a.until)
            print(f"Exception {cur.lastrowid}: {a.agent} may skip {a.rule} until {a.until}.")
        else:
            for r in con.execute("select * from exceptions order by id"):
                print(f"{r['id']:>3} {r['agent_id']:<18} {r['rule']:<20} until {r['until']}: {r['reason']} "
                      f"(approved by {r['approved_by']})")


ORDER = 40


def register(sub) -> dict:
    p = sub.add_parser("report", help="the month's estate report")
    p.add_argument("--month", required=True)
    p.add_argument("--out")
    p = sub.add_parser("discover", help="find unregistered AI in bills, egress logs and code")
    p.add_argument("--bill", action="append", default=[])
    p.add_argument("--egress", action="append", default=[])
    p.add_argument("--scan", action="append", default=[])
    p = sub.add_parser("incident", help="open, end or list incidents")
    p.add_argument("action", choices=["add", "end", "list"])
    p.add_argument("id", nargs="?")
    p.add_argument("--kind", default="incident")
    p.add_argument("--summary", default="")
    p.add_argument("--agent", action="append")
    p.add_argument("--at")
    p.add_argument("--by")
    p = sub.add_parser("exception", help="add or list exceptions (they end on a date)")
    p.add_argument("action", choices=["add", "list"])
    p.add_argument("agent", nargs="?")
    p.add_argument("--rule", default="")
    p.add_argument("--reason", default="")
    p.add_argument("--until", default="")
    p.add_argument("--by")
    return {"report": cmd_report, "discover": cmd_discover, "incident": cmd_incident,
            "exception": cmd_exception}
