"""python -m ops COMMAND ...: one command per module ops/cmd_<name>.py (each module adds its
own command, so a new lesson adds a new file and changes nothing here)."""

import argparse
import importlib
import pkgutil
import sys

import ops


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ops",
        description="Read the ticket service's saved telemetry and operations files.",
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    for info in sorted(pkgutil.iter_modules(ops.__path__), key=lambda m: m.name):
        if info.name.startswith("cmd_"):
            importlib.import_module(f"ops.{info.name}").register(commands)
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        return args.run(args) or 0
    except (FileNotFoundError, ValueError) as error:
        print(f"ops {args.command}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
