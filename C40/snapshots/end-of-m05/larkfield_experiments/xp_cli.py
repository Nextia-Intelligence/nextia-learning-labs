"""The `xp` command: analyse the simulator's runs. Each file in larkfield_experiments/commands/ is one
subcommand (NAME, HELP, add, run, and optionally check)."""

import argparse
import importlib
import pkgutil

from . import commands


def all_commands() -> dict:
    found = {}
    for m in sorted(pkgutil.iter_modules(commands.__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{commands.__name__}.{m.name}")
        found[mod.NAME] = mod
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(prog="xp", description="Analyse Larkfield's experiments (course project).")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    found = all_commands()
    for name, cmd in found.items():
        # argparse formats help with %, so "95% interval" is written "95%% interval" there.
        p = sub.add_parser(name, help=cmd.HELP.replace("%", "%%"), description=cmd.HELP.replace("%", "%%"))
        cmd.add(p)
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return
    found[args.command].run(args)


if __name__ == "__main__":
    main()
