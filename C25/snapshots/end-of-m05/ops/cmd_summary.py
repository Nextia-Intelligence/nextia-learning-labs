"""ops summary FILE: what a saved telemetry file holds (the first command of the course).

    python -m ops summary data/telemetry/normal-week.jsonl.gz

It counts the records, the ticket requests and their answers, the outcomes of the triage
step, the prompt versions, and where the answers come from (replayed or simulated).
"""

from collections import Counter

from ops.telemetry import Telemetry, minutes, share


def register(commands) -> None:
    p = commands.add_parser("summary", help="what a saved telemetry file holds")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.set_defaults(run=run)


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    print(
        f"Records: {len(tel.logs):,} logs, {len(tel.spans):,} spans, {len(tel.metrics):,} metric "
        f"records, from {minutes(tel.start, tel.start)} to {minutes(tel.end, tel.start)}"
    )
    requests = tel.requests()
    codes = Counter(r.get("http.status_code") for r in requests)
    print(
        f"Ticket requests: {len(requests):,} "
        + "("
        + ", ".join(f"{code}: {n:,}" for code, n in sorted(codes.items()))
        + ")"
    )
    triaged = [r["attributes"] for r in tel.events("ticket.triaged")]
    outcomes = Counter(t.get("outcome") for t in triaged)
    print(
        f"Tickets triaged: {len(triaged):,} "
        + "("
        + ", ".join(f"{k}: {n:,}" for k, n in outcomes.most_common())
        + ")"
    )
    if triaged:
        prompts = Counter(t.get("prompt.version") for t in triaged)
        print("Prompt versions: " + ", ".join(f"{k} {n:,}" for k, n in prompts.most_common()))
        evidence = Counter(t.get("evidence") for t in triaged)
        print(
            "Where the answers come from: "
            + ", ".join(f"{k} {n:,} ({share(n, len(triaged))})" for k, n in evidence.most_common())
        )
        needs = sum(t.get("needs_human") is True for t in triaged)
        print(f"Sent to a person (needs_human): {needs:,} ({share(needs, len(triaged))})")
    reviews = tel.events("ticket.reviewed")
    answers = tel.events("answer.served")
    print(
        f"Agents' reviews (delayed labels): {len(reviews):,}; "
        f"answers to questions: {len(answers):,}"
    )
    return 0
