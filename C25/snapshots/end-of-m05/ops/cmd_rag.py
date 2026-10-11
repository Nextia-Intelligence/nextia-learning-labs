"""ops rag FILE: the failures that are special to a language-model service: old sources in
answers, answers with no source, the model version the provider used, and provider errors.

    python -m ops rag data/telemetry/stale-index.jsonl.gz --windows 5

Source freshness: an answer whose sources are not the current version of their documents
(the index was built before a document changed). The model version: what the provider says
in each answer, against what the release expects (--releases folder).
"""

from collections import Counter

from ops.telemetry import Telemetry, minutes, table


def register(commands) -> None:
    p = commands.add_parser("rag", help="old sources, missing sources, model versions, errors")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--windows", type=float, default=5, help="minutes per row (default 5)")
    p.add_argument(
        "--expect-model",
        default="gpt-6-luna-2026-09-22",
        help="the model version that the release expects",
    )
    p.set_defaults(run=run)


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    answers = tel.events("answer.served")
    triaged = tel.events("ticket.triaged")
    retries = tel.events("job.retry")
    print(
        f"{len(answers):,} answers to questions, {len(triaged):,} triaged tickets, "
        f"{len(retries):,} jobs to retry, from {minutes(tel.start, tel.start)} to "
        f"{minutes(tel.end, tel.start)}"
    )
    width = args.windows * 60
    buckets: dict[int, dict] = {}
    for r in answers:
        b = buckets.setdefault(int((r["time"] - tel.start) // width), Counter())
        a = r["attributes"]
        b["answers"] += 1
        b["old sources"] += a.get("stale_sources", 0) > 0
        b["no source"] += not a.get("sources")
        b["index behind"] += a.get("index.version") is not None and a.get("index.version") != a.get(
            "docs.version"
        )
    for r in triaged:
        b = buckets.setdefault(int((r["time"] - tel.start) // width), Counter())
        model = r["attributes"].get("gen_ai.response.model")
        if model:
            b["tickets"] += 1
            b["other model"] += model != args.expect_model
    for r in retries:
        b = buckets.setdefault(int((r["time"] - tel.start) // width), Counter())
        b["provider errors"] += 1
    rows = []
    for k in sorted(buckets):
        b = buckets[k]
        rows.append(
            [
                f"{k * args.windows:g}-{(k + 1) * args.windows:g}",
                b["answers"],
                f"{b['old sources']} ({b['old sources'] / b['answers']:.0%})"
                if b["answers"]
                else "-",
                b["no source"],
                b["index behind"],
                b["tickets"],
                b["other model"],
                b["provider errors"],
            ]
        )
    print(
        table(
            rows,
            [
                "minutes",
                "answers",
                "old sources",
                "no source",
                "index behind",
                "tickets",
                "other model",
                "provider errors",
            ],
        )
    )
    models = Counter(r["attributes"].get("gen_ai.response.model") for r in triaged)
    print(
        "Model versions in the answers: "
        + ", ".join(f"{m} {n:,}" for m, n in models.most_common())
        + f" (the release expects {args.expect_model})"
    )
    return 0
