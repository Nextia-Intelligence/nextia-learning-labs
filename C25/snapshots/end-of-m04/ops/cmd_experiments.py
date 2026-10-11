"""ops experiments: the experiment records (operations/experiments/*.toml): what was changed,
why, the evidence and the decision.

    python -m ops experiments            the list
    python -m ops experiments EXP-001    one record
"""

import tomllib
from pathlib import Path

from ops.telemetry import table

DEFAULT = Path("operations/experiments")


def register(commands) -> None:
    p = commands.add_parser("experiments", help="experiment records and their decisions")
    p.add_argument("id", nargs="?", help="one record, for example EXP-001")
    p.add_argument("--experiments", default=DEFAULT, help="the folder of the records")
    p.set_defaults(run=run)


def records(folder) -> list[dict]:
    out = []
    for path in sorted(Path(folder).glob("*.toml")):
        with path.open("rb") as f:
            out.append(tomllib.load(f))
    return out


def run(args) -> int:
    recs = records(args.experiments)
    if not args.id:
        rows = [
            [r["id"], r["title"], r["owner"], r["status"], r["decision"]["result"]] for r in recs
        ]
        print(table(rows, ["id", "title", "owner", "status", "decision"]))
        return 0
    r = next((r for r in recs if r["id"] == args.id), None)
    if r is None:
        raise ValueError(f"no experiment {args.id} in {args.experiments}")
    print(f"{r['id']}: {r['title']} (asked by {r['asked_by']}, owner {r['owner']}, {r['status']})")
    print(f"Hypothesis: {r['hypothesis']}")
    print(f"Change:     {r['change']}")
    for section in ("evaluation", "results", "decision"):
        print(f"\n[{section}]")
        for k, v in r[section].items():
            print(f"  {k:<28} {v}")
    return 0
