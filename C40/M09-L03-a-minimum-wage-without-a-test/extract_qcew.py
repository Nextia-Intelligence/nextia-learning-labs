"""Extract New Jersey and Pennsylvania restaurant rows from BLS QCEW yearly zips.

Source: US Bureau of Labor Statistics, Quarterly Census of Employment and
Wages (QCEW), "CSVs By Industry", quarterly files. Public domain (BLS:
"everything that we publish ... is in the public domain"; BLS asks to be
cited as the source).

    https://data.bls.gov/cew/data/files/<YEAR>/csv/<YEAR>_qtrly_by_industry.zip

Usage (Python 3.10+, standard library only):

    python extract_qcew.py OUT.csv ZIP1 [ZIP2 ...]        # zips you downloaded
    python extract_qcew.py OUT.csv --download 1990 1991 1992 1993

With --download, the script downloads one year at a time (about 190 MB
each) into a temporary folder, checks its SHA-256, reads it and deletes it
before the next year. It needs about 200 MB of free disk at any moment.

The script reads each zip as it is (no unzip on disk), keeps only:
  - areas: New Jersey (state FIPS 34) and Pennsylvania (42), the state row
    and every county row that the file has;
  - ownership: private (own_code 5); all establishment sizes (size_code 0);
  - industries (NAICS 2002, reconstructed by BLS from SIC records for
    1990-2000): 722211 limited-service restaurants, 7221 full-service
    restaurants, 722 food services and drinking places, 10 all industries;
and writes one row per area, industry, year and quarter, sorted, with the
three monthly employment counts, the number of establishments, the average
weekly wage and the disclosure code. BLS leaves out a county's row when it
would reveal a single employer, so missing counties are the suppressed ones.
"""
from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

INDUSTRIES = {"10", "722", "7221", "722211"}
STATES = ("34", "42")
KEEP = [
    "area_fips", "area_title", "industry_code", "industry_title", "year", "qtr",
    "disclosure_code", "qtrly_estabs_count", "month1_emplvl", "month2_emplvl",
    "month3_emplvl", "avg_wkly_wage",
]
URL = "https://data.bls.gov/cew/data/files/{y}/csv/{y}_qtrly_by_industry.zip"
ZIP_SHA256 = {  # the files as downloaded for the course
    "1990": "5cc9c0f10acd1582e6ed897c81e8d4569b0882718dc7dad7c8efaaa280c725a7",
    "1991": "65091cfccfe17722fe84bd091081e9a46c7d637a6fcdc257a24662fb535f76fd",
    "1992": "ef30c0b4fb784fce27567f4d5db64652088c2265cd57a89c766d91e2af9d1f02",
    "1993": "120e2c25dae9bbf9c7f6bef85f9fc7d2ad8f25a44b5d340fdcc43c6dc7aefbed",
}


def member_code(name: str) -> str:
    # "1992.q1-q4.by_industry/1992.q1-q4 722211 Limited-service restaurants.csv"
    parts = name.rsplit("/", 1)[-1].split(" ")
    return parts[1] if len(parts) > 2 else ""


def rows_from_zip(path) -> list[dict]:
    out = []
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".csv") or member_code(name) not in INDUSTRIES:
                continue
            with zf.open(name) as raw:
                for r in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline="")):
                    if r["area_fips"].startswith(STATES) and r["own_code"] == "5" and r["size_code"] == "0":
                        out.append({k: r[k].strip() for k in KEEP})
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download_year(year: str, folder: Path) -> Path:
    path = folder / f"{year}.zip"
    url = URL.format(y=year)
    print(f"Downloading {url} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (course exercise)"})
    try:
        with urllib.request.urlopen(req) as resp, open(path, "wb") as fh:
            while block := resp.read(1 << 20):
                fh.write(block)
    except OSError:  # Python without certificates (python.org on macOS): try curl
        if subprocess.run(["curl", "-fsSL", "-A", "Mozilla/5.0", "-o", str(path), url]).returncode:
            raise SystemExit(f"Could not download {url}.")
    got = sha256(path)
    if year in ZIP_SHA256 and got != ZIP_SHA256[year]:
        print(f"Note: {year}.zip has SHA-256 {got}, not the course's {ZIP_SHA256[year]}. BLS may have revised it.")
    return path


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    out, rest = args[0], args[1:]
    rows: list[dict] = []
    if rest[0] == "--download":
        for year in rest[1:]:
            with tempfile.TemporaryDirectory() as tmp:  # deleted after each year
                rows.extend(rows_from_zip(download_year(year, Path(tmp))))
    else:
        for path in rest:
            rows.extend(rows_from_zip(path))
    rows.sort(key=lambda r: (r["area_fips"], r["industry_code"], r["year"], r["qtr"]))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEEP, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}: {len(rows):,} rows, SHA-256 {sha256(Path(out))}")


if __name__ == "__main__":
    main()
