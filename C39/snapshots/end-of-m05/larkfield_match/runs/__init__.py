"""Matching runs. Each file in this folder defines RUNS = {name: (dataset, function, description)}.

A run's function takes the project context and returns a pairs table with the columns
`record_id_l, record_id_r, score, match` (match is 1 when the run says "same", else 0).
"""
import importlib
import pkgutil


def all_runs():
    found = {}
    for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{__name__}.{m.name}")
        found.update(getattr(mod, "RUNS", {}))
    return found


def get(name):
    runs = all_runs()
    if name not in runs:
        raise SystemExit(f"No run called {name!r}. Runs you can use: {', '.join(sorted(runs))}")
    return runs[name]
