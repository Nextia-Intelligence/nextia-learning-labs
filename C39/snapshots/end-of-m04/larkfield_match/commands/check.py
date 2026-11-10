"""match check: the setup check of the first module."""

from .. import data, evaluate, pairs
from ..paths import data_dir

NAME = "check"
HELP = "Check the setup: the data files, the exact baseline and its expected pair precision and recall."


def add(p):
    pass


def run(args):
    bad = data.verify()
    if bad:
        raise SystemExit(f"These data files are missing or changed: {', '.join(bad)}. Download the course data again.")
    print(f"Data: {len(data.checksums())} files, checksums right ({data_dir()})")
    exp = data.expected()["exact"]
    df = pairs.get("exact", rebuild=True, quiet=True)
    m = evaluate.pair_measures(df, "customers", "test")
    n = evaluate.entity_count(df, pairs.record_ids("customers"))
    print(f"exact on the test split: pair precision {m['precision']:.3f} (expected {exp['precision']:.3f}), "
          f"recall {m['recall']:.3f} (expected {exp['recall']:.3f})")
    print(f"exact makes {n:,} entities (expected {exp['entities']:,})")
    ok = abs(m["precision"] - exp["precision"]) < 0.0005 and abs(m["recall"] - exp["recall"]) < 0.0005 \
        and n == exp["entities"]
    if not ok:
        raise SystemExit("Setup check failed: see the lesson's troubleshooting list.")
    print("Setup check passed.")
