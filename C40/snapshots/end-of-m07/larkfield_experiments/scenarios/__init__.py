"""The scenarios of the simulator. Each file in this folder is one scenario, with:

    NAME, ABOUT (one line), DEFAULT_SEED, CUSTOMERS (the default size, or None)
    run(seed, customers) -> (tables, truth, meta)

`sim list` shows them; `sim run --scenario NAME` runs one. A later module adds a scenario by adding a file.
"""

import importlib
import pkgutil


def all_scenarios() -> dict:
    out = {}
    for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if m.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{m.name}")
        out[mod.NAME] = mod
    return out
