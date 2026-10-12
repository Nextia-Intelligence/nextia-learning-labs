"""ops canary FILE: the canary against the active release, with the rollback rules of
operations/rollout.toml, ticket by ticket in time order.

    python -m ops canary data/telemetry/canary.jsonl.gz
    python -m ops canary FILE --shadow        the shadow results (no customer saw them)

For each rule it finds the first moment it was met: the minute, and how many canary tickets
(customers) the canary had answered by then. After a rollback it also shows the evidence of
recovery: the tickets after the last release change, by release.
"""

from ops import files
from ops.telemetry import Telemetry, minutes, percentile, table


def register(commands) -> None:
    p = commands.add_parser("canary", help="canary vs active release, with the rollback rules")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--shadow", action="store_true", help="judge the shadow results")
    p.add_argument("--operations", default=files.DEFAULT)
    p.set_defaults(run=run)


def stats(rows: list[dict]) -> dict:
    n = len(rows)
    cost = sum(r.get("cost_usd") or 0 for r in rows)
    lat = [r["triage_ms"] for r in rows if r.get("triage_ms")]
    return {
        "tickets": n,
        "no_answer": sum(r.get("outcome") == "no_answer" for r in rows),
        "cost_per_1000": 1000 * cost / n if n else None,
        "p95_s": (percentile(lat, 95) or 0) / 1000 if lat else None,
        "to_person": sum(r.get("needs_human") is True for r in rows),
    }


def events(tel: Telemetry, shadow: bool) -> tuple[list, list]:
    """(candidate rows, baseline rows), each row: attributes + time + reviewed (if any)."""
    tickets = tel.tickets()
    reviews = {k: t["reviewed"] for k, t in tickets.items() if "reviewed" in t}
    cand, base = [], []
    if shadow:
        for r in tel.events("ticket.shadowed"):
            cand.append(r["attributes"] | {"time": r["time"]})
    for r in tel.events("ticket.triaged"):
        a = r["attributes"] | {
            "time": r["time"],
            "review": reviews.get(r["attributes"].get("ticket.id")),
        }
        if shadow:
            base.append(a)
        else:
            (cand if a.get("release.canary") else base).append(a)
    return cand, base


def agreement(rows: list[dict]) -> tuple[int, int]:
    rv = [r for r in rows if r.get("review")]
    good = sum(
        r.get("outcome") == "ok"
        and r.get("team") == r["review"].get("label.team")
        and r.get("needs_human") == r["review"].get("label.needs_human")
        for r in rv
    )
    return good, len(rv)


def first_breach(cand: list, base: list, rules: dict, minimum: int) -> dict:
    """The first time (in the candidate's order) each rule was met."""
    out = {}
    base_stats = stats(base)
    for i in range(1, len(cand) + 1):
        part = cand[:i]
        s = stats(part)
        t, tickets = part[-1]["time"], i
        if "no answer" not in out and s["no_answer"] >= rules["answers_without_text"]:
            out["no answer"] = (t, tickets)
        if i < minimum:
            continue
        if (
            "cost" not in out
            and base_stats["cost_per_1000"]
            and s["cost_per_1000"] > base_stats["cost_per_1000"] * (1 + rules["cost_increase"])
        ):
            out["cost"] = (t, tickets)
        if (
            "triage time" not in out
            and base_stats["p95_s"]
            and s["p95_s"]
            and s["p95_s"] > base_stats["p95_s"] * (1 + rules["triage_p95_increase"])
        ):
            out["triage time"] = (t, tickets)
    return out


def run(args) -> int:
    rules = files.load("rollout.toml", args.operations)
    tel = Telemetry.load(*args.file)
    cand, base = events(tel, args.shadow)
    if not cand:
        print(
            "No canary tickets in this file (release.canary is never true)."
            if not args.shadow
            else "No shadow results in this file."
        )
        return 1
    who = "shadow" if args.shadow else "canary"
    cs, bs = stats(cand), stats(base)
    cg, cn = agreement(cand)
    bg, bn = agreement(base)
    rows = [
        ["tickets", f"{cs['tickets']:,}", f"{bs['tickets']:,}"],
        [
            "answers without text",
            f"{cs['no_answer']} ({cs['no_answer'] / cs['tickets']:.1%})",
            f"{bs['no_answer']} ({bs['no_answer'] / bs['tickets']:.1%})",
        ],
        [
            "cost per 1,000 tickets (US$)",
            f"{cs['cost_per_1000']:.3f}",
            f"{bs['cost_per_1000']:.3f}",
        ],
        ["triage call p95 (s)", f"{cs['p95_s']:.2f}", f"{bs['p95_s']:.2f}"],
        ["agrees with reviews", f"{cg}/{cn}" if cn else "-", f"{bg}/{bn}" if bn else "-"],
    ]
    label_c = cand[0].get("release.id", who)
    label_b = base[0].get("release.id", "active") if base else "active"
    print(table(rows, ["", f"{who} {label_c}", f"active {label_b}"]))
    breaches = first_breach(cand, base, rules["rollback"], rules["canary"]["minimum_tickets"])
    if not breaches:
        print("No rollback rule was met.")
        return 0
    print("Rollback rules met (first time):")
    for rule, (t, n) in sorted(breaches.items(), key=lambda x: x[1][0]):
        total = sum(1 for r in tel.events("ticket.triaged") if r["time"] <= t)
        print(
            f"  {rule:<12} at {minutes(t, tel.start)}: after {n} {who} tickets "
            f"({total:,} tickets in all)"
        )
    changes = tel.events("release.changed")
    if changes and not args.shadow and not changes[-1]["attributes"].get("release.canary"):
        # The evidence of recovery, once the last change removed the canary. The worker logs
        # the change when it takes its next job. A canary job that started before the change
        # may still finish in the next 30 s: count it as in flight, not as a failed rollback.
        last = changes[-1]
        later = [r for r in tel.events("ticket.triaged") if r["time"] > last["time"]]
        in_flight = [
            r
            for r in later
            if r["attributes"].get("release.canary") and r["time"] <= last["time"] + 30
        ]
        after = [r["attributes"] for r in later if r not in in_flight]
        s = stats(after)
        print(
            f"After the last release change ({minutes(last['time'], tel.start)}: active "
            f"{last['attributes'].get('release.active')}, canary "
            f"{last['attributes'].get('release.canary')}): {s['tickets']:,} tickets, "
            f"{s['no_answer']} without text, US${s['cost_per_1000'] or 0:.3f} per 1,000, "
            f"triage p95 {s['p95_s'] or 0:.2f} s, canary tickets "
            f"{sum(bool(r.get('release.canary')) for r in after)}"
            + (f" ({len(in_flight)} canary tickets in flight finished first)" if in_flight else "")
        )
        if not after:
            print("No ticket was triaged after the change yet: send tickets, then run this again.")
    return 0
