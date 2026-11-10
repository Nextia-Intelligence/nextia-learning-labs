"""xp reset: delete every run (the runs/ folder) to start again. Your code is not touched."""

import shutil

from ..runs import runs_dir

NAME = "reset"
HELP = "delete all runs in runs/ (asks first; --yes to skip the question)"


def add(p):
    p.add_argument("--yes", action="store_true", help="do not ask")


def run(args):
    folder = runs_dir()
    if not folder.exists():
        print(f"Nothing to delete: {folder} does not exist.")
        return
    count = sum(1 for p in folder.iterdir() if p.is_dir())
    if not args.yes and input(f"Delete {folder} with {count} runs? [y/N] ").strip().lower() != "y":
        print("Nothing deleted.")
        return
    shutil.rmtree(folder)
    print(f"Deleted {folder} ({count} runs). Start again with: sim run --scenario email")
