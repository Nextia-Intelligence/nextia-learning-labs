"""Check the data pack before anything uses it: checksums, every file parses, and the
difficulties that the evaluation needs are really there.

    python -m scripts.datapack                 both shops
    python -m scripts.datapack --tenant bramble
    python -m scripts.datapack --folder my-data/acme     your own pack (same layout)

A pack folder has documents/ and inventory.csv (file, doc_id, title, version, effective_from,
effective_to, owner, access, language, doc_type, format).
"""

import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path

from doc_assistant.parse import ParseError, parse

DATA = Path(__file__).resolve().parent.parent / "data"


def check_sums(root: Path) -> tuple[int, list[str]]:
    sums = root / "SHA256SUMS"
    if not sums.exists():
        return 0, []
    bad, n = [], 0
    for line in sums.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        n += 1
        p = root / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(name)
    return n, bad


def report(folder: Path) -> dict:
    with open(folder / "inventory.csv", encoding="utf-8", newline="") as f:
        inventory = list(csv.DictReader(f))
    problems, sections = [], 0
    for row in inventory:
        try:
            doc = parse(row["file"], (folder / row["file"]).read_bytes())
            sections += sum(b.kind == "heading" for b in doc.blocks)
        except (ParseError, FileNotFoundError) as e:
            problems.append(f"{row['file']}: {e}")
    keys = Counter(r["doc_id"] for r in inventory)
    return {
        "documents": len(inventory), "sections": sections,
        "formats": dict(sorted(Counter(r["format"] for r in inventory).items())),
        "staff_only": sum(r["access"] == "staff" for r in inventory),
        "with_versions": sorted(k for k, n in keys.items() if n > 1),
        "end_dated": sum(bool(r["effective_to"]) for r in inventory),
        "supplier": sorted(r["doc_id"] for r in inventory if r["doc_type"] == "supplier"),
        "languages": dict(sorted(Counter(r["language"] for r in inventory).items())),
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.datapack")
    parser.add_argument("--tenant", choices=["all", "larkfield", "bramble"], default="all")
    parser.add_argument("--folder", type=Path)
    args = parser.parse_args(argv)
    folders = [args.folder] if args.folder else [DATA / t for t in (["larkfield", "bramble"] if args.tenant == "all"
                                                                     else [args.tenant])]
    if not args.folder:
        n, bad = check_sums(DATA)
        print(f"Checksums: {n - len(bad)} of {n} files match SHA256SUMS" + (f"; changed: {', '.join(bad)}" if bad else ""))
    failed = 0
    for folder in folders:
        r = report(folder)
        print(f"{folder.name}: {r['documents']} documents, {r['sections']} sections, formats {r['formats']}, "
              f"languages {r['languages']}")
        print(f"  staff-only {r['staff_only']}; with more than one version: {', '.join(r['with_versions']) or 'none'}; "
              f"with an end date {r['end_dated']}; supplier documents: {', '.join(r['supplier']) or 'none'}")
        for p in r["problems"]:
            print(f"  PROBLEM {p}")
        failed += len(r["problems"])
    print("Every document parses." if not failed else f"{failed} documents cannot be parsed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
