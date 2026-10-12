"""ops quality FILE: outcomes, failure categories, tokens, time and cost, side by side for
each prompt version (or release).

    python -m ops quality data/telemetry/release-full.jsonl.gz
    python -m ops quality FILE --by release
    python -m ops quality FILE --from 20 --to 40     only tickets received in those minutes

Outcomes: ok (a valid decision and draft), no_answer (the model used all its tokens and wrote
nothing), bad_answer (text that is not a valid decision), rejected (the provider refused the
request), dead_letter (the provider failed every attempt), failed (other). When agents'
reviews are in the file, it adds how often the decision agreed with them.
"""

from collections import Counter, defaultdict

from ops.telemetry import Telemetry, percentile, table

OUTCOMES = ("ok", "no_answer", "bad_answer", "rejected", "dead_letter", "failed")
KEYS = {"prompt": "prompt.version", "release": "release.id", "evidence": "evidence"}


def register(commands) -> None:
    p = commands.add_parser("quality", help="outcomes, tokens, time and cost by prompt version")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--by", choices=sorted(KEYS), default="prompt")
    p.add_argument("--from", dest="start", type=float, help="from this minute of the file")
    p.add_argument("--to", dest="end", type=float, help="to this minute of the file")
    p.set_defaults(run=run)


def groups(tel: Telemetry, by: str, start=None, end=None) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for t in tel.tickets().values():
        tri = t.get("triaged")
        if tri is None or "received_time" not in t:
            continue
        minute = (t["received_time"] - tel.start) / 60
        if (start is not None and minute < start) or (end is not None and minute >= end):
            continue
        out[str(tri.get(KEYS[by]))].append(t)
    return dict(sorted(out.items()))


def summary(tickets: list[dict]) -> dict:
    tri = [t["triaged"] for t in tickets]
    n = len(tri)
    outcomes = Counter(x.get("outcome") for x in tri)
    ok = [x for x in tri if x.get("outcome") == "ok"]
    answered = [x for x in tri if x.get("gen_ai.usage.output_tokens") is not None]
    reviewed = [t for t in tickets if "reviewed" in t]
    agree = sum(
        t["triaged"].get("outcome") == "ok"
        and t["triaged"].get("team") == t["reviewed"].get("label.team")
        and t["triaged"].get("needs_human") == t["reviewed"].get("label.needs_human")
        for t in reviewed
    )
    return {
        "tickets": n,
        "outcomes": outcomes,
        "needs_human": sum(x.get("needs_human") is True for x in ok),
        "ok": len(ok),
        "tokens_in": percentile([x["gen_ai.usage.input_tokens"] for x in answered], 50),
        "tokens_out": percentile([x["gen_ai.usage.output_tokens"] for x in answered], 50),
        "triage_p50": percentile([x["triage_ms"] for x in tri if x.get("triage_ms")], 50),
        "triage_p95": percentile([x["triage_ms"] for x in tri if x.get("triage_ms")], 95),
        "draft_p95": percentile([x["time_to_draft_s"] for x in ok], 95),
        "cost_per_1000": 1000 * sum(x.get("cost_usd") or 0 for x in tri) / n if n else None,
        "reviewed": len(reviewed),
        "agree": agree,
    }


def part(n: int, whole: int) -> str:
    return f"{n:,} ({n / whole:.1%})"


def num(x) -> str:
    return "-" if x is None else f"{x:,}"


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    g = groups(tel, args.by, args.start, args.end)
    if not g:
        print("No triaged tickets in this file (and these minutes).")
        return 1
    sums = {k: summary(v) for k, v in g.items()}
    names = list(sums)
    rows = [["tickets"] + [f"{sums[k]['tickets']:,}" for k in names]]
    for o in OUTCOMES:
        if any(sums[k]["outcomes"].get(o) for k in names):
            rows.append(
                [f"  {o}"]
                + [part(sums[k]["outcomes"].get(o, 0), sums[k]["tickets"]) for k in names]
            )
    rows.append(
        ["sent to a person"]
        + [
            f"{s['needs_human']:,} ({s['needs_human'] / s['ok']:.1%} of ok)" if s["ok"] else "-"
            for s in sums.values()
        ]
    )
    rows.append(["tokens in (median)"] + [num(s["tokens_in"]) for s in sums.values()])
    rows.append(["tokens out (median)"] + [num(s["tokens_out"]) for s in sums.values()])
    rows.append(
        ["triage call p50 / p95 (s)"]
        + [
            f"{s['triage_p50'] / 1000:.2f} / {s['triage_p95'] / 1000:.2f}"
            if s["triage_p50"] is not None
            else "-"
            for s in sums.values()
        ]
    )
    rows.append(
        ["time to a draft p95 (s)"]
        + [f"{s['draft_p95']:.1f}" if s["draft_p95"] is not None else "-" for s in sums.values()]
    )
    rows.append(
        ["cost per 1,000 tickets (US$)"] + [f"{s['cost_per_1000']:.3f}" for s in sums.values()]
    )
    if any(s["reviewed"] for s in sums.values()):
        rows.append(
            ["agrees with the agent's review"]
            + [
                f"{s['agree']}/{s['reviewed']} ({s['agree'] / s['reviewed']:.1%})"
                if s["reviewed"]
                else "-"
                for s in sums.values()
            ]
        )
    print(table(rows, [args.by] + names))
    return 0
