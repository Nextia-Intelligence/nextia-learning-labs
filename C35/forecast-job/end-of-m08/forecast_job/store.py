"""Keep every weekly plan, and make a run for the same week with the same inputs give the same result.

Each week has its own folder runs/<Monday>/ with the forecast, the totals, the stock order, the roster, the
data checks and run.json. run.json holds a fingerprint of everything the run used (the data it could see,
the settings and the overrides). A second run of the same week:
- with the same fingerprint does nothing: the plan is already there;
- with another fingerprint stops, unless you pass --force (then the old plan is kept in a subfolder).
Old weeks are never deleted: Module 8 compares them with what happened.
"""

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd

from . import __version__, config


def fingerprint(inputs, overrides=None):
    h = hashlib.sha256()
    for df in (inputs.demand, inputs.tickets, inputs.promotions, inputs.price_changes, inputs.products):
        h.update(pd.util.hash_pandas_object(df, index=False).to_numpy().tobytes())
    if overrides is not None and len(overrides):
        h.update(pd.util.hash_pandas_object(overrides, index=False).to_numpy().tobytes())
    settings = {k: v for k, v in vars(config).items() if k.isupper()}
    h.update(json.dumps(settings, sort_keys=True, default=str).encode())
    h.update(__version__.encode())
    return h.hexdigest()[:16]


def week_dir(store, week):
    return Path(store) / str(week.date())


class AlreadyPlanned(Exception):
    pass


def begin(store, week, print_, fp, force=False):
    """Returns the folder to write, or None when the same plan exists."""
    d = week_dir(store, week)
    meta = d / "run.json"
    if meta.exists():
        old = json.loads(meta.read_text())
        if old["fingerprint"] == fp:
            print_(f"Week {week.date()} is already planned with the same inputs ({fp}). Nothing to do.")
            return None
        if not force:
            raise AlreadyPlanned(f"Week {week.date()} was planned with other inputs ({old['fingerprint']}, now {fp}). "
                                 "Run again with --force to replace the plan (the old one is kept).")
        keep = d / f"replaced-{old['fingerprint']}"
        keep.mkdir()
        for f in d.iterdir():
            if f.is_file():
                shutil.move(str(f), keep / f.name)
    d.mkdir(parents=True, exist_ok=True)
    return d


def finish(d, week, fp, summary, problems):
    (d / "checks.txt").write_text("".join(f"warning: {p}\n" for p in problems) or "no problems\n")
    meta = {"week": str(week.date()), "fingerprint": fp, "job_version": __version__, "summary": summary}
    (d / "run.json").write_text(json.dumps(meta, indent=2) + "\n")


def planned_weeks(store):
    return sorted(pd.Timestamp(p.name) for p in Path(store).glob("????-??-??") if (p / "run.json").exists())
