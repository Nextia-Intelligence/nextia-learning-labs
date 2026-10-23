"""Usage and cost: commands of python -m estate."""

from estate.cli import actor as _actor  # noqa: F401


def cmd_usage(a):
    from estate import usage

    if a.last:
        print(usage.last_rows(a.last))
        return
    print(usage.usage_table(a.by, a.month, a.since))



ORDER = 25


def register(sub) -> dict:
    p = sub.add_parser("usage", help="usage and cost from the gateways' records")
    p.add_argument("--by", choices=["agent", "team", "capability", "model", "outcome", "replica"], default="agent")
    p.add_argument("--month")
    p.add_argument("--since")
    p.add_argument("--last", type=int, metavar="N", help="print the last N usage rows, field by field")
    return {"usage": cmd_usage}
