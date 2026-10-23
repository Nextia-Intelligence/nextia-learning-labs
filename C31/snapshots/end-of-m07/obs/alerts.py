"""Service levels and alert rules over saved runs, with windows counted in runs (45 runs: one day at Larkfield).

The rules file (grafana/alerts/rules.json) has the same rules as the Grafana alert rules
(grafana/alerts/agent-alerts.yaml); here they run on saved telemetry, so that every learner can check when
each alert fires and that it stays quiet on a healthy week.

A rule is evaluated after each run closes, over the last `window` closed runs:
    {"uid": ..., "title": ..., "indicator": <name>, "op": ">", "threshold": 0.4, "window": 45, "min_runs": 20,
     "severity": ..., "first_step": ...}
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


def timeline(runs: list, rules: list[dict]) -> dict:
    """For each rule: the periods when it fired, as (start run, start time, end run, end time, peak value)."""
    order = sorted(runs, key=closed_at)
    out = {}
    for rule in rules:
        periods, firing = [], None
        w = rule.get("window", 45)
        for i, run in enumerate(order):
            window = order[max(0, i + 1 - w):i + 1]
            if len(window) < rule.get("min_runs", 1):
                continue
            value = indicators(window)[rule["indicator"]]
            on = _cmp(value, rule["op"], rule["threshold"])
            if on and firing is None:
                firing = {"from_run": i + 1, "from": closed_at(run), "run_id": run.run_id, "peak": value}
            elif on:
                firing["peak"] = max(firing["peak"], value)
            elif firing is not None:
                firing.update({"to_run": i + 1, "to": closed_at(run)})
                periods.append(firing)
                firing = None
        if firing is not None:
            periods.append({**firing, "to_run": None, "to": None})
        out[rule["uid"]] = periods
    return out


def evaluate(runs: list, rules: list[dict]) -> list[str]:
    lines = []
    tl = timeline(runs, rules)
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
            lines.append(f"    from {when(p['from'])} (run {p['from_run']}, {p['run_id']}) {end}; peak {peak}")
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
    reviews = []
    return lines + reviews


def median(xs):
    return statistics.median(xs) if xs else 0.0
