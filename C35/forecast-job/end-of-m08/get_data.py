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
    "demand.csv.gz": "f41d08a5c00c3cc5139fc0f2362073314011e70255bdf115d2ff8c587e128151",
    "orders.csv": "8bec8e70a81e25d326980db77f0d9e03f3f729eeeaba9f107c2972f6985939f2",
    "price_changes.csv": "889b258be4e933b87065d81d0771d6cd9b630ee90223b0a6ab074129c42153cb",
    "products.csv": "198b0a3de6eea8128af68f3cbc3a5c6acd3a64ac854fff18d37660857be8cfbf",
    "promotions.csv": "ca147959faa4c36c757742de7121976ffe79d59b53049dbbc8337a7547541f4a",
    "roster_hourly.csv": "1c1d82917a884b8547f1fe299425f2fa728b0ac9139e0f8205d58e4668b3f6d3",
    "tickets_daily.csv": "67f92e17a4ef6057e6c3b0b81a87bc547645a352afa50912d56486158a23e8da",
    "tickets_hourly.csv.gz": "936be3b84c92dccd907056538a238c5c41a949c782b3b8cfa8409359c3aae509",
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
