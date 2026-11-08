"""search check: the setup check of the first module."""

import json

from .. import compare, data, engine, index, runs
from ..paths import data_dir, index_dir

NAME = "check"
HELP = "Check the setup: the data, the index, one query and the expected NDCG@10 of BM25."


def add(p):
    pass


def run(args):
    bad = data.verify()
    if bad:
        raise SystemExit(f"These data files are missing or changed: {', '.join(bad)}. Download the course data again.")
    print(f"Data: {len(data.checksums())} files, checksums right ({data_dir()})")
    if not (index_dir() / "fts.sqlite").exists():
        meta = index.build_all()
        print(f"Index: built ({meta['products']:,} products, {meta['seconds']} s)")
    else:
        print("Index: found")
    res = runs.get("bm25")("garden hose", None, 10)
    print(f'Query "garden hose": {len(res)} results; first: {res[0][0]} '
          f'{data.catalogue().set_index("product_id").loc[res[0][0], "title"][:50]}')
    expected = json.loads((data_dir() / "expected.json").read_text())["bm25_validation_ndcg10"]
    pq, _ = engine.evaluate("bm25", "validation")
    got = compare.summary(pq)["ndcg@10"]
    print(f"BM25 on the validation queries: NDCG@10 {got:.3f} (expected {expected:.3f})")
    if len(res) != 10 or abs(got - expected) > 0.0005:
        raise SystemExit("Setup check failed: see the lesson's troubleshooting list.")
    print("Setup check passed.")

