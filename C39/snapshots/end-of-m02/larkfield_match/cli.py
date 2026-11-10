"""The `match` command. Each file in larkfield_match/commands/ is one subcommand (NAME, HELP, add, run)."""

import argparse
import importlib
import pkgutil

from . import commands


def main(argv=None):
    parser = argparse.ArgumentParser(prog="match", description="Larkfield's record matching (course project).")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    found = {}
    for m in sorted(pkgutil.iter_modules(commands.__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{commands.__name__}.{m.name}")
        for cmd in getattr(mod, "COMMANDS", [mod]):
            # argparse formats a subcommand's help with %, so "98% of pairs" is written "98%% of pairs" there.
            p = sub.add_parser(cmd.NAME, help=cmd.HELP.replace("%", "%%"), description=cmd.HELP.replace("%", "%%"))
            cmd.add(p)
            found[cmd.NAME] = cmd
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return
    found[args.command].run(args)


if __name__ == "__main__":
    main()
