"""xp check: compare your last analysis of a run with the true effect that the simulator knows."""

from ..runs import load_run
from ..xp_cli import all_commands

NAME = "check"
HELP = "compare the last analysis of a run with the simulator's true effect"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")


def run(args):
    run_ = load_run(args.run)
    analysis = run_.analysis()
    cmd = all_commands().get(analysis["command"])
    if cmd is None or not hasattr(cmd, "check"):
        raise SystemExit(f"xp {analysis['command']} has no check.")
    print(f"Run {run_.folder.name}: the last analysis was `xp {analysis['command']}`.")
    for line in cmd.check(analysis, run_.truth()):
        print(line)
