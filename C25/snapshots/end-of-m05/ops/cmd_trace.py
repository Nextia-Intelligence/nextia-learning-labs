"""ops trace TICKET FILE: from one answer back to every version that made it, and to where its
input came from (the completion check of Module 2).

    python -m ops trace T-500123 data/telemetry/normal-week.jsonl.gz --releases data/releases

It finds the ticket's events in the telemetry, reads the release ID on its triage result,
opens that release manifest, and prints the versions: code, migrations, prompt, schema, model,
retrieval, evaluation set. The input's provenance: the channel, the time, the request ID, the
size and fingerprint of the message (never its text), and, for the course's practice tickets,
which practice ticket it was.
"""

import hashlib
import json
from pathlib import Path

from ops.cmd_release import DEFAULT, read
from ops.telemetry import Telemetry, minutes

PRACTICE = Path("data/practice/tickets.jsonl")


def register(commands) -> None:
    p = commands.add_parser("trace", help="from one answer back to its versions and its input")
    p.add_argument("ticket")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    p.add_argument("--releases", default=DEFAULT, help="the folder of the release manifests")
    p.add_argument("--practice", default=PRACTICE, help="the practice tickets (provenance)")
    p.set_defaults(run=run)


def message_fingerprint(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]


def practice_index(path: Path) -> dict[str, dict]:
    if not Path(path).exists():
        return {}
    rows = [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x]
    return {message_fingerprint(r["message"]): r for r in rows}


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    t = tel.tickets().get(args.ticket)
    if t is None:
        print(f"No ticket {args.ticket} in {', '.join(args.file)}.")
        return 1
    rec = t.get("received", {})
    print(f"Ticket {args.ticket}")
    print(
        f"  input     received {minutes(t['received_time'], tel.start)}, request "
        f"{rec.get('request.id')}, channel {rec.get('ticket.channel')}, "
        f"{rec.get('ticket.message_chars')} characters, language guess "
        f"{rec.get('ticket.language_guess')}"
    )
    fp = rec.get("ticket.message_sha256")
    known = practice_index(args.practice).get(fp) if fp else None
    if known:
        print(
            f"            message fingerprint {fp} = practice ticket {known['case_id']} "
            f"(made up for the evaluation course; split {known['split']}, "
            f"slice {known['slice']})"
        )
    elif fp:
        print(f"            message fingerprint {fp} (not a practice ticket)")
    tri = t.get("triaged")
    if tri is None:
        print("  result    no triage result in this file (still queued, or lost)")
        return 0
    print(
        f"  result    {tri.get('outcome')} after {tri.get('time_to_draft_s')} s: team "
        f"{tri.get('team')}, needs a person {tri.get('needs_human')}, finish "
        f"{tri.get('gen_ai.response.finish_reasons')}, {tri.get('gen_ai.usage.input_tokens')} "
        f"tokens in, {tri.get('gen_ai.usage.output_tokens')} out, US${tri.get('cost_usd'):.6f}"
    )
    print(
        f"            answered by {tri.get('gen_ai.response.model')} ({tri.get('evidence')}), "
        f"prompt {tri.get('prompt.version')}, trace {t.get('triaged_trace') or '-'}"
    )
    rid = tri.get("release.id")
    if not rid:
        print("  release   none: the service ran without RELEASE_ID, so the versions are unknown")
        return 0
    m = read(rid, args.releases)
    c, a, mo, r, d = m["code"], m["assistant"], m["model"], m["retrieval"], m["data"]
    print(f"  release   {rid} ({Path(args.releases) / (rid + '.toml')})")
    print(f"            code {c['version']}, commit {c['commit']}, fingerprint {c['fingerprint']}")
    print(f"            image {c['image']}")
    print(
        f"            migrations {m['database']['migrations']}, "
        f"last {m['database']['last_migration']}"
    )
    print(
        f"            prompt {a['prompt']} (fingerprint {a['prompt_fingerprint']}), schema "
        f"{a['schema']} ({a['schema_fingerprint']}), at most {a['max_completion_tokens']} tokens"
    )
    print(
        f"            model {mo['deployment']}, expected version {mo['expected_version']}, "
        f"embeddings {mo['embedding']}"
    )
    print(f"            retrieval {r['answer_prompt']}, index {r['index_version']}")
    print(
        f"            evaluation set {d['evaluation_set']} (inputs {d['evaluation_inputs']}), "
        f"evidence {d['evidence']}"
    )
    if tri.get("gen_ai.response.model") != mo["expected_version"]:
        print(
            f"  WARNING   the answer came from {tri.get('gen_ai.response.model')}, but the release "
            f"expects {mo['expected_version']}: the provider changed the model"
        )
    return 0
