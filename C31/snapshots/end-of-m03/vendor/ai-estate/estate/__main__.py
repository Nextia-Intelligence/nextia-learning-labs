"""The estate's command line: python -m estate <command> (python -m estate --help lists them).

The commands come from estate/cli/ (one module per part of the estate).
"""

import argparse

from estate.cli import modules


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m estate", description="Larkfield's AI estate")
    sub = ap.add_subparsers(dest="command", required=True)
    handlers = {}
    for m in modules():
        handlers.update(m.register(sub))
    a = ap.parse_args(argv)
    handlers[a.command](a)


if __name__ == "__main__":
    main()
