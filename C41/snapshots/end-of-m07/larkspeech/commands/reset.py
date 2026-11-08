"""`speech reset`: remove your outputs and check that the data files are the course's files."""
import shutil
from pathlib import Path

from larkspeech import data as D
from larkspeech.paths import data_dir


def register(sub):
    p = sub.add_parser("reset", help="remove outputs/, check the data")
    p.set_defaults(run=run)


def run(args):
    removed = [n for n in ("outputs",) if Path(n).exists()]
    for n in removed:
        shutil.rmtree(n)
    n, problems = D.check_files(data_dir(args.data))
    print(f"Reset: removed {', '.join(removed) if removed else 'nothing'}; data: "
          + (f"all {n} files are right." if not problems else f"{len(problems)} problems:"))
    for p in problems[:20]:
        print("  " + p)
    if problems:
        print("Download the data folder again, or copy the broken files from the course's labs repository.")
    return 1 if problems else 0
