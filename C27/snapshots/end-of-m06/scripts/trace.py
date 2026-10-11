"""Show one question's trace as a waterfall (the spans in TRACE_FILE).

    python -m scripts.trace last            the latest question
    python -m scripts.trace <trace_id>
"""

import json
import sys
from pathlib import Path

from doc_assistant.config import PROJECT, settings


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(settings().trace_file)
    path = path if path.is_absolute() else PROJECT / path
    if not path.exists():
        print(f"No traces yet in {path}. Ask a question first.")
        return 1
    spans = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    wanted = argv[0] if argv else "last"
    if wanted == "last":
        # The latest question: its "ask" span is the root in a script, and inside the request's
        # spans (FastAPI makes them) in the API.
        asks = [s for s in spans if s["name"] == "ask"]
        if not asks:
            print("No question in the traces yet.")
            return 1
        wanted = max(asks, key=lambda s: s["end_ns"])["trace_id"]
    mine = sorted((s for s in spans if s["trace_id"] == wanted), key=lambda s: s["start_ns"])
    if not mine:
        print(f"No trace {wanted}.")
        return 1
    by_id = {s["span_id"]: s for s in mine}
    t0 = mine[0]["start_ns"]
    total = max(s["end_ns"] for s in mine) - t0
    print(f"trace {wanted}: {total / 1e6:.0f} ms")
    for s in mine:
        depth, parent = 0, s["parent_id"]
        while parent in by_id:
            depth, parent = depth + 1, by_id[parent]["parent_id"]
        start = (s["start_ns"] - t0) / 1e6
        bar = " " * int(40 * (s["start_ns"] - t0) / total) + "#" * max(1, int(40 * (s["end_ns"] - s["start_ns"]) / total))
        attrs = ", ".join(f"{k}={v}" for k, v in s["attributes"].items())
        print(f"{'  ' * depth}{s['name']:<10} {start:>7.0f} ms +{s['duration_ms']:>7.0f} ms |{bar:<40}| {attrs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
