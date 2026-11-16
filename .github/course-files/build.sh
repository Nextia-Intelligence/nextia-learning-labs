#!/usr/bin/env bash
# Builds one ZIP file per course folder (C02.zip … C42.zip) for the learning
# site's "Download the files" buttons. GitHub can only download the whole
# repository (about 1 GB), so each course gets its own small file.
#
# Usage: build.sh <out-dir> [old-manifest.json]
#
# A course is zipped again only when its folder changed: the manifest keeps
# the git tree hash of each folder. The script writes <out-dir>/manifest.json
# (every course: tree hash and ZIP size in bytes) and the changed ZIP files,
# and prints the names of the ZIP files to upload, one per line.
#
# The ZIP files come from `git archive`, so they hold only committed files,
# inside a top folder with the course's name (C33.zip → C33/…).
set -euo pipefail

out=$1
old=${2:-}
mkdir -p "$out"
[ -n "$old" ] && [ -s "$old" ] || old=

python3 - "$out" "$old" <<'PY'
import json, os, subprocess, sys

out, old = sys.argv[1], sys.argv[2]
previous = json.load(open(old)) if old else {}
folders = subprocess.run(
    ["git", "ls-tree", "-d", "--name-only", "HEAD"], check=True, capture_output=True, text=True
).stdout.split()
courses = sorted(f for f in folders if len(f) == 3 and f[0] == "C" and f[1:].isdigit())

manifest, changed = {}, []
for course in courses:
    tree = subprocess.run(
        ["git", "rev-parse", f"HEAD:{course}"], check=True, capture_output=True, text=True
    ).stdout.strip()
    before = previous.get(course)
    if before and before.get("tree") == tree:
        manifest[course] = before
        continue
    path = os.path.join(out, f"{course}.zip")
    subprocess.run(["git", "archive", "--format=zip", "-9", "-o", path, "HEAD", course], check=True)
    manifest[course] = {"tree": tree, "bytes": os.path.getsize(path)}
    changed.append(f"{course}.zip")

with open(os.path.join(out, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")
print("\n".join(changed))
PY
