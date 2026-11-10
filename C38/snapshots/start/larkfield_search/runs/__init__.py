"""The named search runs: `search query --run NAME`, `search eval --run NAME`.

Each file in this folder registers its runs with @register. A run takes a query text (and its query_id when the
query is in the course's query set, so recorded answers can be used) and returns [(product_id, score)], best
first. Each module of the course adds a file, so `search eval --list` shows what you have built so far.
"""

import importlib
import pkgutil

RUNS = {}


def register(name, about, module=""):
    def wrap(fn):
        RUNS[name] = {"fn": fn, "about": about, "module": module}
        return fn
    return wrap


def load():
    for m in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{m.name}")
    return RUNS


def get(name):
    load()
    if name not in RUNS:
        raise SystemExit(f"No run named {name!r}. Runs: {', '.join(sorted(RUNS))}")
    return RUNS[name]["fn"]
