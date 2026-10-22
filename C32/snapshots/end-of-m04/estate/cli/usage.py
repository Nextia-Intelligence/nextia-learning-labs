"""Usage and cost: commands of python -m estate."""

from estate.cli import actor as _actor  # noqa: F401


def cmd_usage(a):
    from estate import usage

    print(usage.usage_table(a.by, a.month, a.since))



ORDER = 25


def register(sub) -> dict:
    p = sub.add_parser("usage", help="usage and cost from the gateways' records")
    p.add_argument("--by", choices=["agent", "team", "capability", "model", "outcome", "replica"], default="agent")
    p.add_argument("--month")
    p.add_argument("--since")
    return {"usage": cmd_usage}
