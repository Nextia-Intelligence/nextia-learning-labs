"""Read saved telemetry: one JSON record per line, .jsonl or .jsonl.gz (written by the service
with TELEMETRY_FILE; the course's saved scenarios are in this format).

Three kinds of records, as OpenTelemetry has three signals:

    {"signal": "log", "time": ..., "event": "ticket.triaged", "attributes": {...}, ...}
    {"signal": "span", "name": "triage", "start": ..., "end": ..., "trace_id": ...,
                       "span_id": ..., "parent_id": ..., "status": "ok", "attributes": {...}}
    {"signal": "metric", "time": ..., "name": "app.queue.depth", "points": [...]}

Times are seconds since 1970 (UTC). The commands print times as minutes since the first
record ("+12.5 min"), so a saved scenario reads the same on any day.

The logs that matter most are the service's events, one per step of a ticket:
- ticket.received  the API accepted (or refused) a new ticket
- ticket.triaged   the worker finished a ticket's job: outcome, team, needs_human, tokens, cost
- ticket.reviewed  an agent's review arrived later: the team and needs_human that were right
- answer.served    the API answered a question from the shop's documents
"""

import gzip
import json
import math
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


def read_records(path: str | Path) -> Iterator[dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no file {path}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f"{path}, line {n}: not a JSON record") from None


@dataclass
class Telemetry:
    logs: list[dict] = field(default_factory=list)
    spans: list[dict] = field(default_factory=list)
    metrics: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, *paths: str | Path) -> "Telemetry":
        t = cls()
        for path in paths:
            for r in read_records(path):
                {"log": t.logs, "span": t.spans, "metric": t.metrics}.get(
                    r.get("signal"), []
                ).append(r)
        t.logs.sort(key=lambda r: r.get("time", 0))
        t.spans.sort(key=lambda r: r.get("start", 0))
        return t

    @property
    def start(self) -> float:
        times = [r["time"] for r in self.logs] + [r["start"] for r in self.spans]
        return min(times) if times else 0.0

    @property
    def end(self) -> float:
        times = [r["time"] for r in self.logs] + [r["end"] for r in self.spans]
        return max(times) if times else 0.0

    def events(self, name: str) -> list[dict]:
        return [r for r in self.logs if r.get("event") == name]

    def tickets(self) -> dict[str, dict]:
        """One row per ticket: the attributes of its received, triaged and reviewed events
        (prefixed received_, triaged_, reviewed_), and their times."""
        out: dict[str, dict] = {}
        for name, prefix in (
            ("ticket.received", "received"),
            ("ticket.triaged", "triaged"),
            ("ticket.reviewed", "reviewed"),
        ):
            for r in self.events(name):
                tid = r["attributes"].get("ticket.id")
                if not tid:
                    continue
                row = out.setdefault(tid, {"ticket_id": tid})
                row[f"{prefix}_time"] = r["time"]
                row[f"{prefix}_trace"] = r.get("trace_id")
                row[prefix] = r["attributes"]
        return out

    def requests(self) -> list[dict]:
        """Every ticket request the API answered (accepted or refused)."""
        return [r["attributes"] | {"time": r["time"]} for r in self.events("ticket.received")]


def minutes(t: float, start: float) -> str:
    return f"+{(t - start) / 60:.1f} min"


def percentile(values: list[float], p: float) -> float | None:
    """Nearest rank: the smallest value that at least p% of the values are not above."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[rank - 1]


def share(part: int, whole: int) -> str:
    return f"{part / whole:.2%}" if whole else "n/a"


def table(rows: list[list], header: list[str]) -> str:
    """A plain text table, with numbers on the right."""
    cells = [[str(x) for x in header]] + [[str(x) for x in row] for row in rows]
    widths = [max(len(r[i]) for r in cells) for i in range(len(header))]
    numeric = [
        all(_is_number(r[i]) for r in cells[1:]) and len(cells) > 1 for i in range(len(header))
    ]
    lines = []
    for n, r in enumerate(cells):
        lines.append(
            "  ".join(
                c.rjust(w) if numeric[i] else c.ljust(w)
                for i, (c, w) in enumerate(zip(r, widths, strict=True))
            ).rstrip()
        )
        if n == 0:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def _is_number(text: str) -> bool:
    t = text.replace(",", "").replace("%", "").replace("US$", "").replace("+", "").strip()
    try:
        float(t)
        return True
    except ValueError:
        return t in ("", "n/a", "-")
