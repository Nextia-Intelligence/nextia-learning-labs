"""Service levels and alert rules over saved runs, with windows counted in runs (45 runs: one day at Larkfield).

The rules file (grafana/alerts/rules.json) has the same rules as the Grafana alert rules
(grafana/alerts/agent-alerts.yaml); here they run on saved telemetry, so that every learner can check when
each alert fires and that it stays quiet on a healthy week.

A rule is evaluated after each run closes, over the last `window` closed runs:
    {"uid": ..., "title": ..., "indicator": <name>, "op": ">", "threshold": 0.4, "window": 45, "min_runs": 20,
     "severity": ..., "first_step": ..., "example_query": <TraceQL>}
A rule waits until its window holds `min_runs` runs: a share of 2 runs is not a rate (the handoff-rate rule's
false alarm on Monday morning). When a rule fires, the alert names up to three runs behind it (the most recent
first), so that the first click leads to a trace.
"""

import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ = timezone(timedelta(hours=-4))


def closed_at(run) -> int:
    return run.end


def unreconciled(run) -> int:
    """Write calls that timed out and that no reconcile of the same operation followed (in the run)."""
    n = 0
    for w in run.writes:
        if w.get("larkfield.write.outcome") != "timeout":
            continue
        op = w.get("larkfield.operation.id")
        if not any(s.name.startswith("reconcile") and s.get("larkfield.operation.id") == op and s.start >= w.start
                   for s in run.spans):
            n += 1
    return n


def reply_failed(run) -> bool:
    return any(s.get("larkfield.reply.status") == "failed" for s in run.replies)


def loop_stop(run) -> bool:
    return run.stop_reason in ("repeated_call", "max_steps", "too_many_errors")


# For each indicator: the runs that make it go up (the alert's example runs).
CAUSE = {
    "unreconciled_writes": lambda r: unreconciled(r) > 0,
    "reply_failures": reply_failed,
    "loop_stops": loop_stop,
    "handoff_rate": lambda r: r.outcome == "handed_to_person",
    "cost_per_resolved": lambda r: True,          # every run's cost counts: the most expensive ones first
    "resolved_rate": lambda r: r.outcome != "resolved",
    "flagged_runs": lambda r: bool(r.flags),
}


def examples(window: list, indicator: str, n: int = 3) -> list:
    """Up to n runs of the window behind the indicator: the most recent first (the most expensive for cost)."""
    runs = [r for r in window if CAUSE.get(indicator, lambda r: False)(r)]
    if indicator == "cost_per_resolved":
        return sorted(runs, key=lambda r: -r.cost)[:n]
    return sorted(runs, key=closed_at, reverse=True)[:n]


def indicators(window: list) -> dict:
    """The indicators of a window of runs."""
    n = len(window)
    resolved = [r for r in window if r.outcome == "resolved"]
    cost = sum(r.cost for r in window)
    waits = sorted(r.wait_s for r in window if r.wait_s is not None)
    return {
        "runs": n,
        "resolved_rate": len(resolved) / n if n else 0.0,
        "handoff_rate": sum(1 for r in window if r.outcome == "handed_to_person") / n if n else 0.0,
        "cost_per_resolved": cost / len(resolved) if resolved else 0.0,
        "unreconciled_writes": sum(unreconciled(r) for r in window),
        "reply_failures": sum(1 for r in window if reply_failed(r)),
        "loop_stops": sum(1 for r in window if loop_stop(r)),
        "flagged_runs": sum(1 for r in window if r.flags),
        "approval_wait_p95_h": (waits[min(len(waits) - 1, int(0.95 * len(waits)))] / 3600) if waits else 0.0,
    }


def load_rules(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["rules"]


def _cmp(value, op, threshold) -> bool:
    return {">": value > threshold, ">=": value >= threshold, "<": value < threshold}[op]


def when(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, TZ).strftime("%a %d %b %H:%M")


def timeline(runs: list, rules: list[dict], min_runs: int | None = None) -> dict:
    """For each rule: the periods when it fired, as (start run, start time, end run, end time, peak value, example
    runs). min_runs replaces every rule's own minimum (1 = no guard: evaluate from the first run on)."""
    order = sorted(runs, key=closed_at)
    out = {}
    for rule in rules:
        periods, firing = [], None
        w = rule.get("window", 45)
        need = rule.get("min_runs", 1) if min_runs is None else min_runs
        for i, run in enumerate(order):
            window = order[max(0, i + 1 - w):i + 1]
            if len(window) < need:
                continue
            value = indicators(window)[rule["indicator"]]
            on = _cmp(value, rule["op"], rule["threshold"])
            if on and firing is None:
                firing = {"from_run": i + 1, "from": closed_at(run), "run_id": run.run_id, "peak": value,
                          "runs": len(window), "examples": [r.run_id for r in examples(window, rule["indicator"])]}
            elif on:   # the worst value while it fires: the highest, or the lowest for a "<" rule
                firing["peak"] = min(firing["peak"], value) if rule["op"] == "<" else max(firing["peak"], value)
            elif firing is not None:
                firing.update({"to_run": i + 1, "to": closed_at(run)})
                periods.append(firing)
                firing = None
        if firing is not None:
            periods.append({**firing, "to_run": None, "to": None})
        out[rule["uid"]] = periods
    return out


def evaluate(runs: list, rules: list[dict], min_runs: int | None = None) -> list[str]:
    lines = []
    tl = timeline(runs, rules, min_runs)
    for rule in rules:
        periods = tl[rule["uid"]]
        head = f"{rule['uid']:<22} ({rule['indicator']} {rule['op']} {rule['threshold']} over the last {rule.get('window', 45)} runs)"
        if not periods:
            lines.append(f"{head}: quiet")
            continue
        lines.append(f"{head}: FIRED {len(periods)} time(s)")
        for p in periods:
            end = f"until {when(p['to'])} (run {p['to_run']})" if p["to"] else "still firing at the end"
            peak = f"{p['peak']:.4f}" if isinstance(p["peak"], float) else p["peak"]
            worst = "lowest" if rule["op"] == "<" else "peak"
            lines.append(f"    from {when(p['from'])} (run {p['from_run']}, {p['run_id']}) {end}; {worst} {peak}")
            if p["runs"] < rule.get("window", 45):
                lines.append(f"    the window held only {p['runs']} run(s) when it fired")
            if p["examples"]:
                lines.append(f"    example runs: {', '.join(p['examples'])} (python -m obs trace RUN_ID)")
        lines.append(f"    first step: {rule.get('first_step', '')}")
    return lines


def slis(runs: list, window: int = 45) -> list[str]:
    order = sorted(runs, key=closed_at)
    lines = [f"{'window (closed runs)':<34} {'runs':>4} {'resolved':>8} {'handoff':>8} {'US$/resolved':>12} "
             f"{'wait p95 h':>10} {'unrecon.':>8} {'reply fail':>10} {'loops':>5} {'flagged':>7}"]
    for i in range(0, len(order), window):
        w = order[i:i + window]
        x = indicators(w)
        span = f"{when(closed_at(w[0]))} - {when(closed_at(w[-1]))[4:]}"
        lines.append(f"{span:<34} {x['runs']:>4} {x['resolved_rate']:>8.1%} {x['handoff_rate']:>8.1%} "
                     f"{x['cost_per_resolved']:>12.5f} {x['approval_wait_p95_h']:>10.1f} {x['unreconciled_writes']:>8} "
                     f"{x['reply_failures']:>10} {x['loop_stops']:>5} {x['flagged_runs']:>7}")
    x = indicators(order)
    lines.append(f"{'the whole week':<34} {x['runs']:>4} {x['resolved_rate']:>8.1%} {x['handoff_rate']:>8.1%} "
                 f"{x['cost_per_resolved']:>12.5f} {x['approval_wait_p95_h']:>10.1f} {x['unreconciled_writes']:>8} "
                 f"{x['reply_failures']:>10} {x['loop_stops']:>5} {x['flagged_runs']:>7}")
    return lines


def median(xs):
    return statistics.median(xs) if xs else 0.0


# ------------------------------------------------------------------ approvals: the help desk's clock

STAFFED = {"weekday": ((8, 30), (17, 30)), "weekend": ((10, 0), (16, 0))}   # Larkfield's staffed hours (Toronto)


def staffed_seconds(start_ns: int, end_ns: int) -> float:
    """The part of [start, end] that falls in staffed hours: the help desk's clock, which stops at night."""
    a, b = datetime.fromtimestamp(start_ns / 1e9, TZ), datetime.fromtimestamp(end_ns / 1e9, TZ)
    total, day = 0.0, a.replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= b:
        (h1, m1), (h2, m2) = STAFFED["weekday" if day.weekday() < 5 else "weekend"]
        lo, hi = max(a, day.replace(hour=h1, minute=m1)), min(b, day.replace(hour=h2, minute=m2))
        total += max(0.0, (hi - lo).total_seconds())
        day += timedelta(days=1)
    return total


def approvals(runs: list) -> list[dict]:
    """Each approval: when the proposal waited for a person, how long in all, and how long in staffed hours."""
    out = []
    for r in runs:
        if r.wait_s is None:
            continue
        req = [s for s in r.spans if s.name == "approval.request"]
        proposed = req[0].start if req else r.start
        out.append({"run_id": r.run_id, "wait_s": r.wait_s,
                    "staffed_s": staffed_seconds(proposed, proposed + int(r.wait_s * 1e9))})
    return out


def approvals_and_reviews(t, staffed_target_s: float = 3600) -> list[str]:
    """The two indicators that need more than the run counters: the approval wait on the help desk's clock, and
    the sampled reviews (the right outcome, judged by a person)."""
    lines = []
    ap = approvals(list(t.runs.values()))
    if ap:
        ok = sum(1 for a in ap if a["staffed_s"] <= staffed_target_s)
        lines.append(f"Approvals: {len(ap)}; median wait {median([a['wait_s'] for a in ap]) / 60:.1f} min; "
                     f"{sum(1 for a in ap if a['wait_s'] > 8 * 3600)} waited more than 8 h.")
        lines.append(f"In staffed hours only (the clock stops at night): decided within "
                     f"{staffed_target_s / 3600:.0f} h: {ok} of {len(ap)} ({ok / len(ap):.1%}); median "
                     f"{median([a['staffed_s'] for a in ap]) / 60:.1f} min, longest "
                     f"{max(a['staffed_s'] for a in ap) / 60:.1f} min.")
    reviews = reviews_of(t)
    if reviews:
        ok = sum(1 for e in reviews.values() if passed(e))
        lines.append(f"Sampled reviews: {len(reviews)} of {len(t.runs)} runs ({len(reviews) / len(t.runs):.1%}); "
                     f"right outcome {ok} ({ok / len(reviews):.1%}). By slice: python -m obs reviews --by language")
    return lines


# ------------------------------------------------------------------ sampled reviews (quality from live runs)

REVIEW = "gen_ai.evaluation.result"


def sampled(run_id: str, share: float = 0.2) -> bool:
    """The review sampler: a run is picked when the hash of its run ID falls in the first SHARE of 100 buckets
    (the rule of scenarios/week.py). The same run is always picked or never: every service can decide alone."""
    import hashlib
    return int(hashlib.sha256(run_id.encode()).hexdigest(), 16) % 100 < share * 100


def reviews_of(t) -> dict:
    """The last review of each run, joined to the run by the review's trace ID (the run ID if the trace is unknown)."""
    out = {}
    for e in t.events():
        if e["name"] != REVIEW:
            continue
        run = t.find(e["trace_id"]) if e["trace_id"] else None
        rid = run.run_id if run else e["attrs"].get("larkfield.run.id")
        if rid in t.runs:
            out[rid] = e
    return out


def passed(review: dict) -> bool:
    return review["attrs"].get("gen_ai.evaluation.score.label") == "pass"


def review_table(t, key) -> list[str]:
    """Runs, reviews, pass and fail by group: a review is a sample, so the table says how many runs it stands for."""
    reviews = reviews_of(t)
    groups = {}
    for r in t.runs.values():
        groups.setdefault(key(r), []).append(r)
    lines = [f"{'group':<14} {'runs':>5} {'reviewed':>8} {'share':>6} {'pass':>5} {'fail':>5} {'pass rate':>9}"]

    def row(name, rs):
        rv = [reviews[r.run_id] for r in rs if r.run_id in reviews]
        ok = sum(1 for e in rv if passed(e))
        rate = f"{ok / len(rv):.1%}" if rv else "-"
        return f"{name!s:<14} {len(rs):>5} {len(rv):>8} {len(rv) / len(rs):>6.1%} {ok:>5} {len(rv) - ok:>5} {rate:>9}"
    for name, rs in sorted(groups.items(), key=lambda kv: str(kv[0])):
        lines.append(row(name, rs))
    lines.append(row("total", list(t.runs.values())))
    small = [str(k) for k, rs in groups.items() if sum(1 for r in rs if r.run_id in reviews) < 5]
    if small:
        lines.append(f"Fewer than 5 reviews in: {', '.join(sorted(small))}. A pass rate of 1 or 2 reviews says almost "
                     "nothing.")
    return lines
