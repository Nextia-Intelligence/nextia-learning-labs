"""The `recs` command. Each file in larkfield_recs/commands/ is one subcommand (NAME, HELP, add, run)."""

import argparse
import importlib
import pkgutil

from . import commands


def main(argv=None):
    parser = argparse.ArgumentParser(prog="recs", description="Larkfield's recommender (course project).")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    found = {}
    for m in sorted(pkgutil.iter_modules(commands.__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{commands.__name__}.{m.name}")
        for cmd in getattr(mod, "COMMANDS", [mod]):
            # argparse formats a subcommand's help with %, so "95% interval" is written "95%% interval" there.
            p = sub.add_parser(cmd.NAME, help=cmd.HELP.replace("%", "%%"), description=cmd.HELP)
            cmd.add(p)
            found[cmd.NAME] = cmd
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return
    found[args.command].run(args)


if __name__ == "__main__":
    main()
