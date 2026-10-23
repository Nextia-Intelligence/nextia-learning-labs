"""The commands of python -m estate, one module per part of the estate.

Each module has register(sub), which adds its commands to the parser and returns {command: handler}. The
estate grows module by module in the course: a command appears when its module is in the project.
"""

import importlib
import os
import pkgutil


def actor(a) -> str:
    """Who runs the command, for the audit trail (--by, or ESTATE_ACTOR, or the platform owner)."""
    return getattr(a, "by", None) or os.environ.get("ESTATE_ACTOR", "usr-kwame")


def modules() -> list:
    found = [importlib.import_module(f"estate.cli.{m.name}") for m in pkgutil.iter_modules(__path__)]
    return sorted(found, key=lambda m: getattr(m, "ORDER", 99))
