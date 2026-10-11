"""ops slo FILE: the service's SLIs against its SLOs (operations/slos.toml), with the error
budget of each one.

    python -m ops slo data/telemetry/normal-week.jsonl.gz
    python -m ops slo FILE --last 822        only the last 822 tickets (one day)

For each SLO: the SLI (good events ÷ all events), the target, the error budget (how many bad
events the target allows in these events), how many were bad, the share of the budget used,
and the burn rate (how fast the budget is used: 1 = exactly as fast as the target allows;
10 = ten times faster).
"""

from ops import files
from ops.telemetry import Telemetry, minutes, table


def register(commands) -> None:
    p = commands.add_parser("slo", help="SLIs against SLOs, with error budgets")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--last", type=int, help="only the last N tickets")
    p.add_argument("--operations", default=files.DEFAULT, help="the operations folder")
    p.set_defaults(run=run)


def _good_bad(
    slo: dict, requests: list[dict], tickets: list[dict], answers: list[dict], end: float
) -> tuple[int, int]:
    """(good, all) for one SLO."""
    sid = slo["id"]
    if sid == "accept":
        # every request, also the refused ones (a refused ticket was not saved: it has no ID)
        counted = [r for r in requests if not 400 <= r.get("http.status_code", 0) < 500]
        good = [r for r in counted if 200 <= r.get("http.status_code", 0) < 300]
        return len(good), len(counted)
    if sid == "draft":
        limit = slo["threshold_seconds"]
        good = total = 0
        for t in tickets:
            if not 200 <= t["received"].get("http.status_code", 0) < 300:
                continue
            tri = t.get("triaged")
            in_time = tri is not None and tri.get("time_to_draft_s", 1e9) <= limit
            if tri is None and t["received_time"] + limit > end:
                continue  # still within its 10 minutes when the file ends: not decided yet
            total += 1
            good += bool(in_time and tri.get("outcome") == "ok")
        return good, total
    if sid in ("quality", "safety"):
        good = total = 0
        for t in tickets:
            rev = t.get("reviewed")
            if rev is None:
                continue
            tri = t.get("triaged") or {}
            decided = tri.get("outcome") == "ok"
            if sid == "quality":
                total += 1
                good += bool(
                    decided
                    and tri.get("team") == rev.get("label.team")
                    and tri.get("needs_human") == rev.get("label.needs_human")
                )
            elif rev.get("label.needs_human"):
                total += 1
                # a ticket sent to a person without a valid answer (Module 6) reached a person
                reached = tri.get("outcome") in ("ok", "sent_to_person")
                good += bool(reached and tri.get("needs_human") is True)
        return good, total
    if sid == "answer_time":
        limit = slo["threshold_seconds"] * 1000
        return sum(a.get("latency_ms", 1e9) <= limit for a in answers), len(answers)
    if sid == "answer_sources":
        return sum(a.get("stale_sources", 0) == 0 for a in answers), len(answers)
    raise ValueError(f"unknown SLO id {sid!r}")


def evaluate(tel: Telemetry, slos: dict, last: int | None = None) -> dict:
    tickets = sorted(
        (t for t in tel.tickets().values() if "received" in t), key=lambda t: t["received_time"]
    )
    if last:
        tickets = tickets[-last:]
    since = tickets[0]["received_time"] if tickets else tel.start
    requests = [r for r in tel.requests() if r["time"] >= since]
    answers = [r["attributes"] for r in tel.events("answer.served") if r["time"] >= since]
    rows = []
    for slo in slos["slo"]:
        good, total = _good_bad(slo, requests, tickets, answers, tel.end)
        bad = total - good
        target = slo["target"]
        allowed = (1 - target) * total
        rows.append(
            {
                "id": slo["id"],
                "good": good,
                "total": total,
                "bad": bad,
                "sli": good / total if total else None,
                "target": target,
                "allowed": allowed,
                "used": (bad / allowed) if allowed else (None if bad == 0 else float("inf")),
                "burn": ((bad / total) / (1 - target)) if total and target < 1 else None,
                "delayed": slo.get("delayed", False),
                "owner": slo["owner"],
            }
        )
    triaged = [t["triaged"] for t in tickets if "triaged" in t]
    cost = sum(t.get("cost_usd", 0.0) for t in triaged)
    return {
        "tickets": len(tickets),
        "since": since,
        "rows": rows,
        "cost_per_1000": 1000 * cost / len(triaged) if triaged else None,
        "budget_per_1000": slos["budget"]["cost_per_1000_tickets_usd"],
    }


def _pct(x: float | None, digits: int = 2) -> str:
    return "n/a" if x is None else f"{x:.{digits}%}"


def run(args) -> int:
    slos = files.load("slos.toml", args.operations)
    tel = Telemetry.load(*args.file)
    result = evaluate(tel, slos, args.last)
    print(
        f"{result['tickets']:,} tickets, {minutes(result['since'], tel.start)} to "
        f"{minutes(tel.end, tel.start)}; objectives from {args.operations}/slos.toml"
    )
    rows = []
    for r in result["rows"]:
        used = r["used"]
        used_text = (
            "n/a" if used is None else ("no budget" if used == float("inf") else f"{used:.0%}")
        )
        rows.append(
            [
                r["id"] + (" *" if r["delayed"] else ""),
                f"{_pct(r['sli'])} ({r['good']:,}/{r['total']:,})",
                _pct(r["target"], 1),
                f"{r['allowed']:.1f}",
                r["bad"],
                used_text,
                "n/a" if r["burn"] is None else f"{r['burn']:.2f}",
                r["owner"],
            ]
        )
    print(
        table(rows, ["SLO", "SLI (good/all)", "target", "budget", "bad", "used", "burn", "owner"])
    )
    print("* from agents' reviews, which arrive later (delayed labels)")
    if result["cost_per_1000"] is not None:
        over = result["cost_per_1000"] > result["budget_per_1000"]
        print(
            f"Cost: US${result['cost_per_1000']:.3f} per 1,000 tickets (budget "
            f"US${result['budget_per_1000']:.2f}{', OVER' if over else ''})"
        )
    return 0
