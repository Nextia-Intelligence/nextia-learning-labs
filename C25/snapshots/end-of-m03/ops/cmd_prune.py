"""ops prune FILE --days N: keep only the records of the last N days (retention).

    python -m ops prune telemetry/ticket-worker.jsonl --days 30

Telemetry is kept only as long as it is useful (TELEMETRY_RETENTION_DAYS, 30 by default):
older records are deleted from the file. The Grafana stack has its own retention settings
(observability/README.md).
"""

import gzip
import json
import time
from pathlib import Path

from ops.telemetry import read_records


def register(commands) -> None:
    p = commands.add_parser("prune", help="delete records older than the retention")
    p.add_argument("file")
    p.add_argument("--days", type=float, required=True)
    p.add_argument("--now", type=float, help="seconds since 1970 (default: the clock)")
    p.set_defaults(run=run)


def run(args) -> int:
    limit = (args.now or time.time()) - args.days * 86400
    kept, dropped = [], 0
    for r in read_records(args.file):
        t = r.get("time", r.get("end", 0))
        if t >= limit:
            kept.append(r)
        else:
            dropped += 1
    path = Path(args.file)
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept)
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(text.encode("utf-8")))
    else:
        path.write_text(text, encoding="utf-8")
    print(f"{path}: kept {len(kept):,} records, deleted {dropped:,} older than {args.days:g} days")
    return 0
