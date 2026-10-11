"""The course's command line: python -m adapt COMMAND [options]. python -m adapt --help lists the commands."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS: dict = {}


def command(name: str, help: str, *arguments):
    def wrap(func):
        COMMANDS[name] = (func, help, arguments)
        return func
    return wrap


def arg(*names, **options):
    return names, options


def split_arg(default="dev"):
    return arg("--split", default=default, help="dev, holdout or contaminated; several with commas (dev,holdout)")


def splits_of(args) -> tuple[str, ...]:
    splits = tuple(args.split.split(","))
    if "holdout" in splits:
        print("Note: the holdout cases are for the final decision only. Read them once, at the end.")
    return splits


# Start: the evaluation cases

@command("cases", "count the evaluation cases by split and slice")
def cmd_cases(args):
    from .cases import SPLITS, load_cases, version

    cases = load_cases(SPLITS)
    print(f"{len(cases)} cases, version {version()} (the evaluation course's set)")
    for split in SPLITS:
        part = [c for c in cases if c.split == split]
        slices = {}
        for c in part:
            slices[c.slice] = slices.get(c.slice, 0) + 1
        needs = sum(c.needs_human for c in part)
        print(f"  {split:13s} {len(part):3d}  needs a person {needs:2d}  "
              + ", ".join(f"{k} {v}" for k, v in sorted(slices.items())))


@command("show", "show one evaluation case", arg("case_id"))
def cmd_show(args):
    from .cases import SPLITS, load_cases, model_input

    case = next((c for c in load_cases(SPLITS) if c.case_id == args.case_id), None)
    if case is None:
        raise SystemExit(f"No case {args.case_id}")
    print(f"{case.case_id} ({case.split}, {case.slice}, {case.language})")
    print(f"expected: team {case.team or '(none)'}, needs_human {str(case.needs_human).lower()}"
          + (f" (rule {case.rule})" if case.rule else ""))
    print()
    print(model_input(case))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m adapt", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (func, help_text, arguments) in COMMANDS.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        for names, options in arguments:
            p.add_argument(*names, **options)
        p.set_defaults(func=func)
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
