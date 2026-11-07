"""Get the course's payments file into data/ and check its SHA-256.

    python scripts/get_data.py                 download from the labs repository on GitHub
    python scripts/get_data.py --from FOLDER   copy from a folder you already have (for example a clone of
                                               the labs repository: nextia-learning-labs/C34/data)

Standard library only. The data is synthetic: no real people, no real cards.
"""
import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path

LABS = "https://raw.githubusercontent.com/Nextia-Intelligence/nextia-learning-labs/main/C34/data/"
FILES = ["payments.csv.gz"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", help="a folder that has payments.csv.gz and SHA256SUMS")
    args = ap.parse_args()
    out = Path("data")
    out.mkdir(exist_ok=True)
    for name in ["SHA256SUMS"] + FILES:
        if args.src:
            shutil.copyfile(Path(args.src) / name, out / name)
        else:
            urllib.request.urlretrieve(LABS + name, out / name)
    sums = dict(reversed(line.split()) for line in (out / "SHA256SUMS").read_text().splitlines() if line.strip())
    for name in FILES:
        if sha256(out / name) != sums[name]:
            raise SystemExit(f"{name} has the wrong SHA-256. Delete data/ and run this again.")
        print(f"OK {name} ({(out / name).stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
