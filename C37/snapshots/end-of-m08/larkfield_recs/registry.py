"""Every recommendation method by name. Each file in larkfield_recs/methods/ adds its methods to METHODS."""

import importlib
import pkgutil

from . import methods


def all_methods():
    """{name: (class, default settings, description)} from every file in methods/."""
    out = {}
    for m in sorted(pkgutil.iter_modules(methods.__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{methods.__name__}.{m.name}")
        out.update(getattr(mod, "METHODS", {}))
    return out


def make(name, period, settings=None):
    table = all_methods()
    if name not in table:
        raise SystemExit(f"Unknown method {name!r}. Methods: {', '.join(table)}")
    cls, defaults, _ = table[name]
    return cls(period, **{**defaults, **(settings or {})})


def parse_settings(pairs):
    """["factors=64", "alpha=0.5"] -> {"factors": 64, "alpha": 0.5}."""
    out = {}
    for pair in pairs or []:
        key, _, value = pair.partition("=")
        for conv in (int, float):
            try:
                value = conv(value)
                break
            except ValueError:
                pass
        if value in ("true", "false"):
            value = value == "true"
        out[key.strip()] = value
    return out
