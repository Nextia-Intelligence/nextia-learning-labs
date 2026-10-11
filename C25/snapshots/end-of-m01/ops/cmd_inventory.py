"""ops inventory: what the service depends on, its version, its owner and the first sign of a
failure (operations/inventory.toml)."""

from ops import files
from ops.telemetry import table


def register(commands) -> None:
    p = commands.add_parser("inventory", help="what the service depends on, and who owns it")
    p.add_argument("--operations", default=files.DEFAULT, help="the operations folder")
    p.add_argument("--owner", help="only the components of this person")
    p.add_argument("--versions", action="store_true", help="where to read each version")
    p.set_defaults(run=run)


def run(args) -> int:
    parts = files.load("inventory.toml", args.operations)["component"]
    if args.owner:
        parts = [c for c in parts if c["owner"].lower() == args.owner.lower()]
    last = "version (where to read it)" if args.versions else "first sign of a failure"
    key = "version" if args.versions else "first_sign"
    rows = [[c["kind"], c["name"], c["owner"], c[key]] for c in parts]
    print(table(rows, ["kind", "component", "owner", last]))
    owners = sorted({c["owner"] for c in parts})
    print(f"\n{len(parts)} components, {len(owners)} owners: {', '.join(owners)}.")
    return 0
