"""The `route` command. Each command lives in larkroute/commands/<name>.py with an `add(subparsers)` function;
a new file there is a new command.

    route --help
"""

import argparse
import importlib
import pkgutil

from larkroute import commands

ORDER = ["info", "compare", "reset", "agreement", "explain", "cascade", "llm", "calibration", "zones",
         "corrections", "train", "serve", "drift", "release"]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="route", description="Larkfield's message router (synthetic course data).")
    sub = p.add_subparsers(dest="command", required=True)
    names = [m.name for m in pkgutil.iter_modules(commands.__path__)]
    for name in sorted(names, key=lambda n: (ORDER.index(n) if n in ORDER else len(ORDER), n)):
        importlib.import_module(f"{commands.__name__}.{name}").add(sub)
    return p


def main(argv=None) -> None:
    args = parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
