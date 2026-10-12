"""Ask one question in the terminal, as a member of a shop (the same pipeline as the API).

    python -m scripts.ask "Can a customer return a book after 20 days?" --tenant bramble
    python -m scripts.ask "What is the staff discount?" --tenant larkfield --user usr-omar
    python -m scripts.ask "..." --as-of 2026-12-10 --json
"""

import argparse
import json

from doc_assistant.pipeline import ask

from .common import STAFF, as_member, open_deps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.ask")
    parser.add_argument("question")
    parser.add_argument("--tenant", default="larkfield")
    parser.add_argument("--user", help="default: Sam (Larkfield) or Ines (Bramble Books)")
    parser.add_argument("--as-of")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    deps = open_deps()
    who = as_member(deps, args.user or STAFF.get(args.tenant, "usr-sam"), args.tenant)
    result = ask(deps, who, args.question, args.as_of)
    deps.db.close()
    if args.json:
        print(json.dumps(result.__dict__, indent=1, ensure_ascii=False))
        return 0
    print(f"{who.name} ({who.role}) at {who.shop} asks: {args.question}")
    found = ", ".join(f"{p['chunk_id']} {p['doc_key']} v{p['version']}" for p in result.passages)
    print(f"Passages found: {found or 'none'}")
    print(f"Answer ({'answerable' if result.answerable else 'not answerable'}): {result.answer}")
    for c in result.claims:
        cites = "; ".join(f"{x['title']}, {x['section'] or 'start'}, v{x['version']}" for x in c["citations"])
        checks = f"  checks: {', '.join(c['problems'])}" if c["problems"] else ""
        print(f"  - {c['text']} [{cites or 'no citation'}]{checks}")
    if result.note:
        print(f"Note: {result.note}")
    print(f"{result.provider} {result.model} | {result.latency_ms} ms | tokens {result.input_tokens} in, "
          f"{result.output_tokens} out | US${result.cost_usd:.6f} | trace {result.trace_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
