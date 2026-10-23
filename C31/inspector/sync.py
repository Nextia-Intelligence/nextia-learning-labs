"""Copy the course project's rules and saved data into the run inspector.

The inspector uses the SAME code as the course project's `obs` tool for the runs, the five flags, the
audit story and the audit store. These files are copied here byte for byte. Do not change the copies
by hand: change the project's file, then run this script again.

    python sync.py                    copy from the project folder that is found (see below)
    python sync.py --project PATH     copy from this project folder
    python sync.py --check            only compare; exit code 1 if a copy is different or missing

The project folder is, in this order: --project, the environment variable INSPECTOR_PROJECT,
../project (beside this folder), ../snapshots/end-of-m08 (the labs layout).
"""

import argparse
import filecmp
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE / "larkfield_inspector"

# project file -> copy in the package (byte-identical)
CODE = {
    "obs/model.py": "vendor/obs/model.py",
    "obs/flags.py": "vendor/obs/flags.py",
    "obs/story.py": "vendor/obs/story.py",
    "auditstore/store.py": "vendor/auditstore/store.py",
    "auditstore/schema.py": "vendor/auditstore/schema.py",
    # story.py reads data/people.json beside its package folder
    "data/people.json": "vendor/data/people.json",
}
# project folder -> built-in saved data in the package (whole folder)
DATA = {
    "data/telemetry/week": "data/week",
    "data/telemetry/healthy-week": "data/healthy-week",
    "data/telemetry/constructed": "data/constructed",
}


def find_project(given: str | None = None) -> Path | None:
    candidates = [given, os.environ.get("INSPECTOR_PROJECT"), HERE.parent / "project",
                  HERE.parent / "snapshots" / "end-of-m08"]
    for c in candidates:
        if c and (Path(c) / "obs" / "flags.py").exists():
            return Path(c).resolve()
    return None


def _files(folder: Path) -> list[str]:
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() and p.name != ".DS_Store")


def differences(project: Path) -> list[str]:
    """What is different between the project and the copies (empty list: all the same)."""
    out = []
    for src, dst in CODE.items():
        a, b = project / src, PACKAGE / dst
        if not b.exists():
            out.append(f"missing copy: {dst}")
        elif not filecmp.cmp(a, b, shallow=False):
            out.append(f"different: {dst} (project file {src})")
    for src, dst in DATA.items():
        a, b = project / src, PACKAGE / dst
        if not b.exists():
            out.append(f"missing data folder: {dst}")
            continue
        fa, fb = _files(a), _files(b)
        if fa != fb:
            out.append(f"different files in {dst}: {sorted(set(fa) ^ set(fb))}")
            continue
        for name in fa:
            if not filecmp.cmp(a / name, b / name, shallow=False):
                out.append(f"different: {dst}/{name}")
    return out


def sync(project: Path) -> None:
    for src, dst in CODE.items():
        target = PACKAGE / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / src, target)
        print(f"copied {src} -> larkfield_inspector/{dst}")
    for src, dst in DATA.items():
        target = PACKAGE / dst
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(project / src, target, ignore=shutil.ignore_patterns(".DS_Store"))
        print(f"copied {src}/ -> larkfield_inspector/{dst}/ ({len(_files(target))} files)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", help="the course project folder")
    ap.add_argument("--check", action="store_true", help="compare only")
    args = ap.parse_args(argv)
    project = find_project(args.project)
    if project is None:
        print("No project folder found. Give it with --project PATH or INSPECTOR_PROJECT.", file=sys.stderr)
        return 2
    if args.check:
        diff = differences(project)
        for line in diff:
            print(line)
        print("The copies are the same as the project's files." if not diff else f"{len(diff)} difference(s).")
        return 1 if diff else 0
    sync(project)
    return 0


if __name__ == "__main__":
    sys.exit(main())
