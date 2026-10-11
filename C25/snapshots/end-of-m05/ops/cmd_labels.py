"""ops labels FILE: the delayed labels (agents' reviews) and the quick signals to watch until
they arrive.

    python -m ops labels data/telemetry/drift.jsonl.gz --windows 500

For each window of tickets (by arrival): how many were reviewed, how often the assistant
agreed with the review (with a 95% interval), and the proxy signals that are known at once:
answers without text, the share sent to a person, the share of French messages. It also says
how many reviews a margin of 5 points needs.
"""

from collections import defaultdict

from ops import stats
from ops.telemetry import Telemetry, percentile, table


def register(commands) -> None:
    p = commands.add_parser("labels", help="agents' reviews (delayed labels) and proxy signals")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--windows", type=int, default=500, help="tickets per window (default 500)")
    p.add_argument("--by", choices=["window", "prompt", "release"], default="window")
    p.set_defaults(run=run)


def agree(t: dict) -> bool:
    tri, rev = t.get("triaged") or {}, t["reviewed"]
    return (
        tri.get("outcome") == "ok"
        and tri.get("team") == rev.get("label.team")
        and tri.get("needs_human") == rev.get("label.needs_human")
    )


def french(ts: list[dict]) -> float:
    return sum(t["received"].get("ticket.language_guess") == "fr" for t in ts) / len(ts)


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    tickets = sorted(
        (t for t in tel.tickets().values() if "received" in t), key=lambda t: t["received_time"]
    )
    reviewed = [t for t in tickets if "reviewed" in t]
    delays = [
        t["reviewed"].get("review.delay_s") for t in reviewed if t["reviewed"].get("review.delay_s")
    ]
    print(
        f"{len(tickets):,} tickets, {len(reviewed):,} reviewed "
        f"({len(reviewed) / max(1, len(tickets)):.0%}); review delay median "
        f"{percentile(delays, 50) or 0:,.0f} s, p95 {percentile(delays, 95) or 0:,.0f} s"
    )
    groups: dict[str, list[dict]] = defaultdict(list)
    if args.by == "window":
        n = args.windows
        for i, t in enumerate(tickets):
            groups[f"{i // n * n + 1:>6}-{(i // n + 1) * n}"].append(t)
    else:
        key = {"prompt": "prompt.version", "release": "release.id"}.get(args.by)
        for t in tickets:
            groups[str((t.get("triaged") or {}).get(key))].append(t)
    rows = []
    for name, ts in groups.items():
        rv = [t for t in ts if "reviewed" in t]
        good = sum(agree(t) for t in rv)
        lo, hi = stats.wilson(good, len(rv))
        tri = [t["triaged"] for t in ts if "triaged" in t]
        ok = [x for x in tri if x.get("outcome") == "ok"]
        rows.append(
            [
                name,
                len(ts),
                len(rv),
                f"{good / len(rv):.1%} [{lo:.1%}, {hi:.1%}]" if rv else "-",
                f"{sum(x.get('outcome') == 'no_answer' for x in tri) / max(1, len(tri)):.1%}",
                f"{sum(x.get('needs_human') is True for x in ok) / max(1, len(ok)):.1%}",
                f"{french(ts):.1%}",
            ]
        )
    print(
        table(
            rows,
            [
                args.by,
                "tickets",
                "reviewed",
                "agrees (95% interval)",
                "no answer",
                "to a person",
                "French",
            ],
        )
    )
    print(
        "Reviews arrive later: the last windows have fewer. For a margin of about 5 points on an "
        f"agreement near 90%, a window needs {stats.reviews_needed(0.9, 0.05)} reviews."
    )
    return 0
