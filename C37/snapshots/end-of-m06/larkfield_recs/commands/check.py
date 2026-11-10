"""recs check: is the setup right? Data files, a known first result."""

import json

from .. import data, harness
from ..paths import data_dir

NAME = "check"
HELP = "Check the setup: the data files and a known result (popular on the validation period)."


def add(p):
    pass


def run(args):
    bad = data.verify()
    if bad:
        raise SystemExit(f"These data files are missing or changed: {', '.join(bad)}. Download the data again.")
    print(f"Data: {len(data.checksums())} files, all right ({data_dir()})")
    res, _, _ = harness.run("popular", "validation", quick=True)
    want = json.loads((data_dir() / "expected.json").read_text()).get("popular_validation_quick_recall10")
    if want is None:
        print(f"popular on the validation period (quick): recall@10 {res['recall']:.3f} (no expected value for "
              "this validation period)")
        print("Data check passed. The result check needs the default periods: use `recs info` to see yours.")
        return
    print(f"popular on the validation period (quick): recall@10 {res['recall']:.3f} (expected {want:.3f})")
    if abs(res["recall"] - want) > 0.0005:
        raise SystemExit("The result is not the expected one. Run `recs reset` and try again.")
    print("Setup check passed.")
