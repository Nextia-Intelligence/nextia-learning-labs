"""xp check: compare your last analysis of a run with the true effect that the simulator knows."""

from ..runs import load_analysed_run
from ..xp_cli import all_commands

NAME = "check"
HELP = "compare the last analysis of a run with the simulator's true effect"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the run you analysed last)")


def run(args):
    run_ = load_analysed_run(args.run)
    analysis = run_.analysis()
    cmd = all_commands().get(analysis["command"])
    if cmd is None or not hasattr(cmd, "check"):
        raise SystemExit(f"xp {analysis['command']} has no check.")
    print(f"Run {run_.folder.name}: the last analysis was `xp {analysis['command']}`.")
    truth = run_.truth()
    note = truth.get("planted") if isinstance(truth.get("planted"), str) else ""
    no_truth = ("No truth for this run: the simulator did not make it, or it has no true effect for "
                f"`xp {analysis['command']}`." + (f" {note}" if note else ""))
    if set(truth) <= {"planted"}:
        raise SystemExit(no_truth)
    try:
        lines = cmd.check(analysis, truth)
    except KeyError:
        raise SystemExit(no_truth) from None
    for line in lines:
        print(line)
