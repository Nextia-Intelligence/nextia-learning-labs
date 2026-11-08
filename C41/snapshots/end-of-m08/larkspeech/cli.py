"""The `speech` command. Each file in larkspeech/commands/ adds one or more subcommands, so a later snapshot of
the project adds commands by adding files."""
import argparse
import importlib
import pkgutil
import sys

import larkspeech.commands as commands


def build_parser():
    p = argparse.ArgumentParser(prog="speech", description="Larkfield's speech tools (Speech AI course).")
    p.add_argument("--data", help="the data folder (default: $LARKSPEECH_DATA, ./data, ../data or ../../data)")
    sub = p.add_subparsers(dest="command", required=True)
    for m in sorted(pkgutil.iter_modules(commands.__path__), key=lambda m: m.name):
        importlib.import_module(f"larkspeech.commands.{m.name}").register(sub)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        code = args.run(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        code = 2
    sys.exit(code or 0)
