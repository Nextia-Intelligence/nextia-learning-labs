"""ops alerts FILE: run the service's alert rules (operations/alerts.toml) on saved telemetry,
every 10 seconds of the file, as Grafana does on live data.

    python -m ops alerts data/telemetry/canary.jsonl.gz
    python -m ops alerts FILE --after "rollout canary"     detection time after that action
    python -m ops alerts FILE --after "simulator mode: outage"

For each alert: when it fired, when it stopped, and the owner and runbook. With --after, it
also prints how long after that practice action each alert fired (the detection time). The
action is found by its text as ops incident prints it ("simulator mode: outage"), so a part of
it is enough; the first action that matches counts. The
values come from the events, so they can differ a little from Grafana's (which reads metrics
that are sent every 15 seconds).
"""

import bisect

from ops import files
from ops.telemetry import Telemetry, minutes, percentile, table

STEP = 10.0


class Series:
    """Events in time order, to take the ones in a window quickly."""

    def __init__(self, rows: list[dict]):
        self.rows = sorted(rows, key=lambda r: r["time"])
        self.times = [r["time"] for r in self.rows]

    def window(self, t: float, seconds: float) -> list[dict]:
        return self.rows[
            bisect.bisect_right(self.times, t - seconds) : bisect.bisect_right(self.times, t)
        ]


def build(tel: Telemetry) -> dict:
    def attrs(name):
        return Series([r["attributes"] | {"time": r["time"]} for r in tel.events(name)])

    tickets = tel.tickets()
    open_tickets = sorted(
        (t["received_time"], t.get("triaged_time", float("inf")))
        for t in tickets.values()
        if "received" in t and 200 <= t["received"].get("http.status_code", 0) < 300
    )
    breaker = [
        (r["time"], r["attributes"].get("breaker.state")) for r in tel.events("breaker.changed")
    ]
    return {
        "received": attrs("ticket.received"),
        "triaged": attrs("ticket.triaged"),
        "answers": attrs("answer.served"),
        "reviews": attrs("ticket.reviewed"),
        "open": open_tickets,
        "breaker": breaker,
    }


def value(uid: str, rule: dict, s: dict, t: float) -> float | None:
    w = rule["window"]
    if uid == "accept-fast-burn":
        rows = [
            r for r in s["received"].window(t, w) if not 400 <= r.get("http.status_code", 0) < 500
        ]
        return sum(r.get("http.status_code", 0) >= 500 for r in rows) / len(rows) if rows else None
    if uid == "draft-fast-burn":
        rows = s["triaged"].window(t, w)
        return sum(r.get("outcome") != "ok" for r in rows) / len(rows) if rows else None
    if uid == "no-answer":
        # a ticket sent to a person by the fallback also had no valid answer
        return sum(
            r.get("outcome") in ("no_answer", "sent_to_person") for r in s["triaged"].window(t, w)
        )
    if uid == "drafts-late":
        waiting = [received for received, done in s["open"] if received <= t < done]
        return t - min(waiting) if waiting else 0.0
    if uid == "provider-circuit-open":
        state = "closed"
        for when, st in s["breaker"]:
            if when <= t:
                state = st
        return 1.0 if state == "open" else 0.0
    if uid == "cost-over-budget":
        rows = s["triaged"].window(t, w)
        return 1000 * sum(r.get("cost_usd") or 0 for r in rows) / len(rows) if rows else None
    if uid == "triage-slow":
        lat = [r["triage_ms"] for r in s["triaged"].window(t, w) if r.get("triage_ms")]
        return (percentile(lat, 95) or 0) / 1000 if lat else None
    if uid == "model-version-changed":
        expected = rule.get("expected_model")
        return sum(
            r.get("gen_ai.response.model") not in (None, expected)
            for r in s["triaged"].window(t, w)
        )
    if uid == "old-sources":
        return sum(r.get("stale_sources", 0) > 0 for r in s["answers"].window(t, w))
    if uid == "reviews-disagree":
        rows = s["reviews"].window(t, w)
        return sum(r.get("agrees") is False for r in rows) / len(rows) if rows else None
    raise ValueError(f"no rule for alert {uid}")


def evaluate(tel: Telemetry, rules: list[dict]) -> dict[str, list[tuple[float, float | None]]]:
    """For each alert, the intervals (fired at, resolved at or None) in seconds since 1970."""
    s = build(tel)
    out: dict[str, list] = {}
    for rule in rules:
        uid, since, firing, intervals = rule["uid"], None, False, []
        t = tel.start
        while t <= tel.end:
            v = value(uid, rule, s, t)
            breached = v is not None and v > rule["above"]
            if breached:
                since = t if since is None else since
                if not firing and t - since >= rule["for"]:
                    firing = True
                    intervals.append([t, None])
            else:
                since = None
                if firing:
                    intervals[-1][1] = t
                    firing = False
            t += STEP
        out[uid] = [tuple(i) for i in intervals]
    return out


def action_text(attributes: dict) -> str:
    """A practice action as ops incident prints it: "simulator mode: outage"."""
    detail = attributes.get("mode") or attributes.get("alert") or attributes.get("model_version")
    return attributes.get("action", "") + (f": {detail}" if detail else "")


def register(commands) -> None:
    p = commands.add_parser("alerts", help="run the alert rules on saved telemetry")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--after", help="a practice action (its name): detection times after it")
    p.add_argument("--operations", default=files.DEFAULT)
    p.set_defaults(run=run)


def run(args) -> int:
    rules = files.load("alerts.toml", args.operations)["alert"]
    tel = Telemetry.load(*args.file)
    fired = evaluate(tel, rules)
    since = None
    if args.after:
        acts = [
            (r["time"], action_text(r["attributes"]))
            for r in tel.events("practice.action")
            if args.after in action_text(r["attributes"])
        ]
        if not acts:
            raise ValueError(f"no practice action like {args.after!r} in the file")
        since = acts[0][0]
        print(f"Practice action {acts[0][1]!r} at {minutes(since, tel.start)}")
    rows = []
    for rule in rules:
        for start, end in fired[rule["uid"]]:
            detect = (
                f"{(start - since) / 60:.1f} min" if since is not None and start >= since else "-"
            )
            rows.append(
                [
                    rule["uid"],
                    rule["severity"],
                    minutes(start, tel.start),
                    minutes(end, tel.start) if end else "still firing",
                    detect,
                    rule["owner"],
                ]
            )
    if not rows:
        print("No alert fired.")
        return 0
    print(table(rows, ["alert", "severity", "fired", "resolved", "after the action", "owner"]))
    return 0
