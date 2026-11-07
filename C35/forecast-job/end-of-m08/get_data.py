"""Download the Larkfield data into data/ and check every file's SHA-256. Standard library only.

    python get_data.py

The data is synthetic: it was made for the forecasting course and has no real people, products or prices.
It comes from the course's public labs repository on GitHub.
"""

import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/Nextia-Intelligence/nextia-learning-labs/main/C35/data/"
FILES = {
    "calendar.csv": "a5d1d5a3b640a983de72a30fca0e627a4ef23e797b1d80619e9ffcaadf118844",
    "demand.csv.gz": "8b39303985cbdb9bb1f3c705cd927ed6aaeb6f9665bd56ad4c3f8cb2b8578c99",
    "orders.csv": "bd8059fd73fe294daa157f8a6b6ae3f58319fa644eaa7ff0d31122b02cf05e30",
    "price_changes.csv": "889b258be4e933b87065d81d0771d6cd9b630ee90223b0a6ab074129c42153cb",
    "products.csv": "198b0a3de6eea8128af68f3cbc3a5c6acd3a64ac854fff18d37660857be8cfbf",
    "promotions.csv": "ca147959faa4c36c757742de7121976ffe79d59b53049dbbc8337a7547541f4a",
    "roster_hourly.csv": "6c2e0e96881b36ded52ed19458515c71f025288ddaebd589b50c82a8ad7fa69b",
    "tickets_daily.csv": "36f7067db060fdd2bd084c408c0622370a012773849f243020336f1fc678b31d",
    "tickets_hourly.csv.gz": "43f7fbb3e360a8e4a0cb4e101ea6a6242a76f0c37204d76ee9413ea3adbedd92",
    "weather.csv": "43a199a8b235940e291195bfd026901b62a10189b29f3a3ad9527b5382544276",
}
DATA = Path(__file__).resolve().parent / "data"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    DATA.mkdir(exist_ok=True)
    for name, expected in FILES.items():
        path = DATA / name
        if path.exists() and sha256(path) == expected:
            continue
        try:
            urllib.request.urlretrieve(URL + name, path)
        except OSError:
            if subprocess.run(["curl", "-fsSL", "-o", str(path), URL + name]).returncode:
                sys.exit(f"Could not download {name}. Check your internet connection and run again.")
        if sha256(path) != expected:
            sys.exit(f"{name} has the wrong checksum. Delete data/{name} and run again.")
    print(f"Ready: {len(FILES)} files in {DATA.name}/, every checksum is right.")


if __name__ == "__main__":
    main()
