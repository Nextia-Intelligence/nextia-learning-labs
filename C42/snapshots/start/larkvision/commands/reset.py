"""`vision reset`: remove your outputs and the review folder, and check the data files."""
import shutil
from pathlib import Path

from larkvision import data as D
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("reset", help="remove outputs/ and review/, check the data")
    p.set_defaults(run=run)


def run(args):
    removed = [n for n in ("outputs", "review") if Path(n).exists()]
    for n in removed:
        shutil.rmtree(n)
    n, problems = D.check_files(data_dir(args.data))
    print(f"Reset: removed {', '.join(removed) if removed else 'nothing'}; data: "
          + ("all " + str(n) + " files are right." if not problems else f"{len(problems)} problems:"))
    for p in problems[:20]:
        print("  " + p)
    return 1 if problems else 0
