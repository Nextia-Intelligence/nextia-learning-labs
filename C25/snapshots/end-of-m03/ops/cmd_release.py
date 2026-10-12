"""ops release: build, read, compare and check release manifests (operations/releases/).

python -m ops release build --prompt assistant-v2              print a manifest
python -m ops release build --prompt assistant-v2 --write      ... and save it
python -m ops release list
python -m ops release show 1.5.0-3f9a1c
python -m ops release diff 1.5.0-3f9a1c 1.5.0-8b20d4           what changed, setting by setting
python -m ops release verify 1.5.0-3f9a1c                      do the files still match it?
"""

import os
import tomllib
from pathlib import Path

from ops.telemetry import table

DEFAULT = Path("operations/releases")


def register(commands) -> None:
    p = commands.add_parser("release", help="build, read, compare and check release manifests")
    sub = p.add_subparsers(dest="action", metavar="ACTION", required=True)
    b = sub.add_parser("build", help="make the manifest of the files in this folder")
    b.add_argument("--prompt", default="assistant-v2", help="the triage prompt's file name")
    b.add_argument("--image", help="the container image digest (the release workflow sets it)")
    b.add_argument("--evidence", default="", help="the evaluation run that supports it")
    b.add_argument("--index-version", default="", help="the retrieval index's version")
    b.add_argument("--commit", help="the Git commit (default: read it with git)")
    b.add_argument("--write", action="store_true", help="save it in the releases folder")
    for name in ("list", "show", "diff", "verify"):
        s = sub.add_parser(name)
        if name in ("show", "verify"):
            s.add_argument("release")
        if name == "diff":
            s.add_argument("old")
            s.add_argument("new")
    for s in sub.choices.values():
        s.add_argument("--releases", default=DEFAULT, help="the folder of the manifests")
    p.set_defaults(run=run)


def read(release_id: str, folder) -> dict:
    path = Path(folder) / f"{release_id}.toml"
    if not path.exists():
        raise FileNotFoundError(f"no release manifest {path}")
    with path.open("rb") as f:
        return tomllib.load(f)


def flat(manifest: dict) -> dict:
    return {
        f"{section}.{k}": v
        for section, items in manifest.items()
        if isinstance(items, dict)
        for k, v in items.items()
    }


def run(args) -> int:
    from ticket_api import releases  # the service's own code makes the manifest

    folder = Path(args.releases)
    if args.action == "build":
        settings = {k: os.environ[k] for k in releases.BEHAVIOUR if os.environ.get(k)}
        manifest = releases.build(
            args.prompt,
            image=args.image or "not built (the course runs the service with Python)",
            evidence=args.evidence,
            index_version=args.index_version,
            settings=settings,
            commit=args.commit,
        )
        text = releases.to_toml(manifest)
        print(text, end="")
        if args.write:
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{manifest['id']}.toml"
            path.write_text(text, encoding="utf-8")
            print(f"\nSaved {path}. Run the service with RELEASE_ID={manifest['id']}")
        return 0
    if args.action == "list":
        rows = []
        for path in sorted(folder.glob("*.toml")):
            with path.open("rb") as f:
                m = tomllib.load(f)
            rows.append(
                [
                    m["id"],
                    m["assistant"]["prompt"],
                    m["model"]["expected_version"],
                    m["database"]["last_migration"],
                    m["data"]["evidence"],
                ]
            )
        print(table(rows, ["release", "prompt", "model version", "last migration", "evidence"]))
        return 0
    if args.action == "show":
        m = read(args.release, folder)
        print(f"Release {m['id']} ({folder}/{m['id']}.toml)")
        for key, value in flat(m).items():
            print(f"  {key:<32} {value}")
        return 0
    if args.action == "diff":
        old, new = flat(read(args.old, folder)), flat(read(args.new, folder))
        rows = [
            [k, old.get(k, "-"), new.get(k, "-")]
            for k in sorted(old.keys() | new.keys())
            if old.get(k) != new.get(k)
        ]
        print(f"{len(rows)} of {len(old.keys() | new.keys())} settings differ:")
        print(table(rows, ["setting", args.old, args.new]))
        return 0
    if args.action == "verify":
        m = read(args.release, folder)
        release = releases.Release(
            m["id"], m["assistant"]["prompt"], m["assistant"]["prompt_fingerprint"], m
        )
        problems = releases.check(release)
        code = releases.code_fingerprint()
        if code != m["code"]["fingerprint"]:
            problems.append(
                f"code: the manifest has fingerprint {m['code']['fingerprint']}, the "
                f"files here have {code} (a file changed after the release)"
            )
        if problems:
            print(f"Release {m['id']} does NOT match the files here:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"Release {m['id']} matches the files here (code, prompt, migrations).")
        return 0
    return 2
