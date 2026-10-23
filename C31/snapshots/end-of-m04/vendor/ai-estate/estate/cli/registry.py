"""The registry and the agent lifecycle: commands of python -m estate."""

import json
import sys

from estate.cli import actor as _actor


def _print_reg(reg):
    f = reg.form
    print(f"{reg.agent_id} | {f['name']} | {reg.status} | version {reg.version}")
    print(f"  owner {f['owner']} ({f['team']}) | risk {f['risk_tier']} | autonomy {f['autonomy']} | "
          f"data {', '.join(f['data_classes'])}")
    print(f"  capabilities: {', '.join(f['capabilities']) or 'none'}")
    print(f"  tools: {', '.join(f['tools']) or 'none'}")
    lim = f.get("limits") or {}
    print(f"  budget US${f['budget_usd_month']}/month | {lim.get('requests_per_minute')} requests/min | "
          f"{lim.get('tokens_per_day'):,} tokens/day | {lim.get('max_calls_per_run')} model calls per run")
    for cap, pin in (f.get("pins") or {}).items():
        print(f"  pin: {cap} -> {pin['deployment']} {pin.get('model_version', '')} until {pin['retire_by']}")
    print(f"  review by {f['review_date']} | credentials: "
          + (", ".join(f"{c['client_id']} ({'revoked ' + c['revoked_at'] if c['revoked_at'] else 'active'})"
                       for c in reg.credentials) or "none"))


def cmd_check(a):
    from estate import registry

    problems = registry.check_form(registry.read_form(a.file))
    print("\n".join(f"- {p}" for p in problems) if problems else "The form is complete.")
    if problems:
        sys.exit(1)


def cmd_register(a):
    from estate import registry

    try:
        reg = registry.register(registry.read_form(a.file), _actor(a))
    except registry.FormError as e:
        sys.exit("Not registered:\n" + "\n".join(f"- {p}" for p in e.problems))
    print(f"Registered {reg.agent_id} (version {reg.version}): {reg.status}"
          + (" until a review approves it (python -m estate review " + reg.agent_id + ")" if reg.status == "pending"
             else ""))


def cmd_list(a):
    from estate import registry

    regs = registry.all_registrations()
    for r in regs:
        f = r.form
        print(f"{r.agent_id:<20} {r.status:<10} {f['risk_tier']:<7} {f['team']:<11} {f['owner']:<11} "
              f"{', '.join(f['capabilities']) or '-'}")
    print(f"{len(regs)} registrations")


def cmd_show(a):
    from estate import registry

    reg = registry.get(a.id)
    if reg is None:
        sys.exit(f"No registration {a.id}.")
    _print_reg(reg)


def cmd_set_status(a, status):
    from estate import configstore, registry

    try:
        reg = registry.set_status(a.id, status, _actor(a), a.reason)
    except (KeyError, ValueError) as e:
        sys.exit(str(e))
    print(f"{reg.agent_id} is now {reg.status}.")
    ok, asked = configstore.push()
    if asked:
        print(f"Told {ok} of {asked} gateway replicas to refresh now.")


def cmd_review(a):
    from estate import registry

    try:
        reg = registry.review(a.id, _actor(a), a.next, not a.reject, a.note or "")
    except (KeyError, registry.FormError) as e:
        sys.exit(str(e))
    print(f"Reviewed {reg.agent_id}: {reg.status}, next review by {reg.form['review_date']}.")


def cmd_review_due(a):
    from datetime import date

    from estate import registry

    items = registry.review_due(date.fromisoformat(a.today) if a.today else None, a.within)
    for reg, why in items:
        print(f"{reg.agent_id:<20} {why}")
    print(f"{len(items)} item(s) need attention")


def cmd_events(a):
    from estate import registry

    for e in reversed(registry.events(a.id, a.limit)):
        print(f"{e['at']}  {e['agent_id'] or '-':<18} {e['action']:<20} {e['actor']:<11} "
              f"{json.dumps(e['detail'], ensure_ascii=False)}")


ORDER = 20


def register(sub) -> dict:
    p = sub.add_parser("check", help="check a registration form")
    p.add_argument("file")
    p = sub.add_parser("register", help="register an agent from its form (or a new version)")
    p.add_argument("file")
    p.add_argument("--by")
    sub.add_parser("list", help="every registration")
    p = sub.add_parser("show", help="one registration")
    p.add_argument("id")
    for name in ("suspend", "resume", "retire", "drain"):
        p = sub.add_parser(name, help=f"{name} an agent")
        p.add_argument("id")
        p.add_argument("--reason", required=True)
        p.add_argument("--by")
    p = sub.add_parser("review", help="review a registration and set the next review date")
    p.add_argument("id")
    p.add_argument("--next", required=True, help="the next review date, for example 2027-01-15")
    p.add_argument("--reject", action="store_true")
    p.add_argument("--note")
    p.add_argument("--by")
    p = sub.add_parser("review-due", help="overdue reviews, owners who left, pins that retire")
    p.add_argument("--today")
    p.add_argument("--within", type=int, default=30)
    p = sub.add_parser("events", help="the registry's audit trail")
    p.add_argument("id", nargs="?")
    p.add_argument("--limit", type=int, default=50)
    return {"check": cmd_check, "register": cmd_register, "list": cmd_list, "show": cmd_show,
            "suspend": lambda a: cmd_set_status(a, "suspended"), "resume": lambda a: cmd_set_status(a, "active"),
            "retire": lambda a: cmd_set_status(a, "retired"), "drain": lambda a: cmd_set_status(a, "draining"),
            "review": cmd_review, "review-due": cmd_review_due, "events": cmd_events}
