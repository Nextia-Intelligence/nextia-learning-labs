"""ops gate CANDIDATE: the release gate. Offline evidence and operational limits, one decision.

    python -m ops gate assistant-v3
    python -m ops gate assistant-v2      the live prompt passes its own gate?

It reads operations/evidence/<prompt>.json (the evaluation course's results on the frozen
holdout tickets), the baseline's evidence (--baseline, the live prompt) and the limits in
operations/gates.toml. Any failed line means DO NOT SHIP; a blocker (a critical case without
an answer) fails the gate even when the averages look fine.
"""

import json
from pathlib import Path

from ops import files
from ops.telemetry import table


def register(commands) -> None:
    p = commands.add_parser("gate", help="the release gate: evidence and limits, one decision")
    p.add_argument("candidate", help="a prompt version, for example assistant-v3")
    p.add_argument("--baseline", default="assistant-v2")
    p.add_argument("--operations", default=files.DEFAULT)
    p.set_defaults(run=run)


def evidence(folder, prompt: str) -> dict:
    path = Path(folder) / "evidence" / f"{prompt}.json"
    if not path.exists():
        raise FileNotFoundError(f"no evidence {path}: evaluate {prompt} first")
    return json.loads(path.read_text(encoding="utf-8"))


def decide(c: dict, b: dict, g: dict) -> list[list]:
    caught, of = c["needs_human_caught"]
    diff = c.get("decisions_difference_vs_baseline") or [0.0, 0.0, 0.0]
    # The baseline against itself. Not "the same prompt": a model change keeps the prompt.
    if c["run"] == b["run"]:
        diff = [0.0, 0.0, 0.0]
    checks = [
        (
            "blockers (critical cases failed)",
            len(c["blockers"]),
            "<=",
            g["blockers"]["blockers_max"],
            "; ".join(c["blockers"]) or "none",
        ),
        (
            "answers without text (holdout)",
            c["answers_without_text"],
            "<=",
            g["blockers"]["answers_without_text_max"],
            f"of {c['cases']} tickets",
        ),
        (
            "decisions: lower end of (candidate - baseline)",
            diff[1],
            ">=",
            g["quality"]["decisions_difference_min"],
            f"{diff[0]:+.3f} [{diff[1]:+.3f}, {diff[2]:+.3f}]",
        ),
        (
            "needs a person: share caught",
            caught / of,
            ">=",
            g["quality"]["needs_human_recall_min"],
            f"{caught} of {of}",
        ),
        (
            "cost per 1,000 tickets (US$)",
            c["cost_per_1000_usd"],
            "<=",
            g["operations"]["cost_per_1000_usd_max"],
            f"baseline {b['cost_per_1000_usd']}",
        ),
        (
            "triage time p95 (s)",
            c["latency_p95_s"],
            "<=",
            g["operations"]["latency_p95_s_max"],
            f"baseline {b['latency_p95_s']}",
        ),
    ]
    rows = []
    for name, value, op, limit, note in checks:
        ok = value <= limit if op == "<=" else value >= limit
        shown = f"{value:.3f}" if isinstance(value, float) else str(value)
        rows.append([name, shown, f"{op} {limit}", "pass" if ok else "FAIL", note])
    return rows


def run(args) -> int:
    g = files.load("gates.toml", args.operations)
    c, b = evidence(args.operations, args.candidate), evidence(args.operations, args.baseline)
    rows = decide(c, b, g)
    print(
        f"Release gate for {args.candidate} (baseline {args.baseline}), evidence: {c['run']} "
        f"on the {c['split']} split of {c['evaluation_set']}"
    )
    print(table(rows, ["check", "value", "limit", "result", "detail"]))
    failed = [r[0] for r in rows if r[3] == "FAIL"]
    if failed:
        print(f"Decision: DO NOT SHIP ({len(failed)} failed: {', '.join(failed)})")
        return 1
    print("Decision: SHIP to a canary (the canary's own checks come next: python -m ops canary)")
    return 0
