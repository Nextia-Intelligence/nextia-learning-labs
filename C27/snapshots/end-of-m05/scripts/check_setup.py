"""Check that this computer is ready for the capstone (the first command of the course).

    python -m scripts.check_setup

It checks; it changes nothing. Each line says OK, or what to do.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return p.returncode, (p.stdout or p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def checks() -> list[tuple[str, bool, str]]:
    out = []
    v = sys.version_info
    out.append(("Python 3.12 or newer", v >= (3, 12), f"{v.major}.{v.minor}.{v.micro}" if v >= (3, 12)
                else f"{v.major}.{v.minor}: install Python 3.12 or newer"))
    code, text = run(["git", "--version"])
    out.append(("Git", code == 0, text if code == 0 else "install Git (the Git course shows how)"))
    if shutil.which("docker"):
        code, text = run(["docker", "version", "--format", "{{.Server.Version}}"])
        out.append(("Docker is running", code == 0, f"Docker Engine {text}" if code == 0
                    else "start Docker Desktop (or the Docker service), then run this again"))
        code, text = run(["docker", "compose", "version", "--short"])
        out.append(("Docker Compose", code == 0, text if code == 0 else "install Docker Compose v2"))
    else:
        out.append(("Docker", False, "install Docker Desktop (the containers course shows how)"))
    free = shutil.disk_usage(ROOT).free / 1e9
    out.append(("5 GB of free disk", free >= 5, f"{free:.0f} GB free" if free >= 5
                else f"only {free:.1f} GB free: the models and images need about 5 GB"))
    templates = sorted(p.name for p in (ROOT / "docs" / "templates").glob("*.md"))
    out.append(("Design-pack templates", len(templates) >= 8, f"{len(templates)} templates in docs/templates/"))
    return out


def main() -> int:
    results = checks()
    width = max(len(name) for name, _, _ in results)
    for name, ok, text in results:
        print(f"{'OK  ' if ok else 'TODO'}  {name:<{width}}  {text}")
    missing = sum(not ok for _, ok, _ in results)
    print("Ready for the capstone." if not missing else f"{missing} thing(s) to do before you start.")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
