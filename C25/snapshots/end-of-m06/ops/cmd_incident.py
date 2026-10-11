"""ops incident FILE: the timeline of an incident, and the evidence that the service recovered.

    python -m ops incident data/telemetry/outage.jsonl.gz
    python -m ops incident FILE --minute 1        one row per minute (default 2)

It puts on one timeline: the practice actions (what we did on purpose), release changes, the
circuit breaker, the alerts (the rules of operations/alerts.toml run on the file), and per
period the tickets received, refused, finished, without a valid draft, the oldest waiting
ticket and the time to a draft. The recovery checks at the end compare the last period with
the first: a recovery is a claim, and these numbers are its evidence.
"""

from ops import files
from ops.cmd_alerts import build, evaluate
from ops.telemetry import Telemetry, minutes, percentile, table


def register(commands) -> None:
    p = commands.add_parser("incident", help="an incident's timeline and recovery evidence")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--minute", type=float, default=2, help="minutes per row (default 2)")
    p.add_argument("--operations", default=files.DEFAULT)
    p.set_defaults(run=run)


def period(tel: Telemetry, s: dict, a: float, b: float) -> dict:
    rec = [r for r in s["received"].rows if a <= r["time"] < b]
    tri = [r for r in s["triaged"].rows if a <= r["time"] < b]
    ok = [r for r in tri if r.get("outcome") == "ok"]
    waiting = [x for x, done in s["open"] if x <= b < done]
    return {
        "received": len(rec),
        "refused": sum(r.get("http.status_code", 0) >= 500 for r in rec),
        "finished": len(tri),
        "not_ok": len(tri) - len(ok),
        "oldest": b - min(waiting) if waiting else 0.0,
        "draft_p95": percentile([r["time_to_draft_s"] for r in ok], 95),
    }


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    rules = files.load("alerts.toml", args.operations)["alert"]
    s = build(tel)
    marks = []
    for r in tel.events("practice.action"):
        a = r["attributes"]
        detail = a.get("mode") or a.get("alert") or a.get("model_version") or ""
        text = a.get("action", "") + (f": {detail}" if detail else "")
        marks.append((r["time"], "practice" if "alert" not in text else "grafana", text))
    for r in tel.events("release.changed"):
        a = r["attributes"]
        text = f"release: active {a.get('release.active')}"
        if a.get("release.canary"):
            text += f", canary {a['release.canary']} ({a.get('release.canary_share', 0):.0%})"
        marks.append((r["time"], "release", text))
    for r in tel.events("breaker.changed"):
        marks.append((r["time"], "breaker", f"circuit {r['attributes'].get('breaker.state')}"))
    for uid, intervals in evaluate(tel, rules).items():
        for start, end in intervals:
            marks.append((start, "alert", f"{uid} fired"))
            if end:
                marks.append((end, "alert", f"{uid} resolved"))
    marks.sort()
    # several workers report the same breaker change: keep one line per change
    marks = [
        m
        for i, m in enumerate(marks)
        if not (i and m[1:] == marks[i - 1][1:] and m[0] - marks[i - 1][0] < 5)
    ]
    print("Timeline (what happened, in order):")
    print(
        table(
            [
                [minutes(t, tel.start), kind, text]
                for t, kind, text in marks
                if not text.startswith("ops rollout status")
            ],
            ["when", "kind", "event"],
        )
    )
    width = args.minute * 60
    rows, periods = [], []
    t = tel.start
    while t < tel.end:
        p = period(tel, s, t, t + width)
        periods.append(p)
        rows.append(
            [
                f"{(t - tel.start) / 60:g}-{(t - tel.start + width) / 60:g}",
                p["received"],
                p["refused"],
                p["finished"],
                p["not_ok"],
                f"{p['oldest']:.0f}",
                f"{p['draft_p95']:.1f}" if p["draft_p95"] is not None else "-",
            ]
        )
        t += width
    print("\nPer period (minutes):")
    print(
        table(
            rows,
            [
                "minutes",
                "received",
                "refused (5xx)",
                "finished",
                "no valid draft",
                "oldest waiting (s)",
                "time to draft p95 (s)",
            ],
        )
    )
    full = [p for p in periods if p["finished"]]
    if len(full) >= 2:
        first, last = full[0], full[-1]
        print("\nRecovery checks (the last full period against the first):")
        checks = [
            ("tickets are accepted", last["refused"] == 0, f"{last['refused']} refused"),
            (
                "drafts are valid",
                last["not_ok"] <= first["not_ok"],
                f"{last['not_ok']} without a valid draft (first period {first['not_ok']})",
            ),
            (
                "nothing is waiting long",
                last["oldest"] <= 120,
                f"oldest waiting {last['oldest']:.0f} s",
            ),
            (
                "drafts are on time",
                (last["draft_p95"] or 0) <= max(2 * (first["draft_p95"] or 0), 30),
                f"p95 {last['draft_p95'] or 0:.1f} s "
                f"(first period {first['draft_p95'] or 0:.1f} s)",
            ),
        ]
        for name, ok, detail in checks:
            print(f"  [{'x' if ok else ' '}] {name}: {detail}")
    return 0
