"""Reads and checks the YAML test cases."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CHECKS = {
    "contains", "contains_any", "not_contains", "regex", "not_regex", "language", "cites", "not_cites",
    "retrieved", "not_retrieved", "tool_called", "tool_not_called", "no_error", "refuses", "max_chars",
    "order_status", "judge",
}
KEYS = {"id", "title", "tags", "customer", "steps", "message", "variants", "relation", "checks", "turn", "runs",
        "pass", "status", "bug", "notes"}


class CaseError(Exception):
    pass


@dataclass
class Case:
    id: str
    title: str
    file: Path
    steps: list[str]
    checks: list[dict]
    customer: str | None = None
    variants: list[str] = field(default_factory=list)
    relation: str = "same_results"
    turn: int | None = None
    runs: int | None = None
    pass_rule: object = "all"
    status: str = "active"
    bug: str | None = None
    tags: list[str] = field(default_factory=list)

    def required(self, runs: int) -> int:
        """How many runs must pass."""
        rule = self.pass_rule
        if rule in ("all", None):
            return runs
        if isinstance(rule, str) and "/" in rule:
            k, n = rule.split("/")
            return min(runs, round(int(k) * runs / int(n)))
        if isinstance(rule, (int, float)) and 0 < float(rule) <= 1:
            return min(runs, -(-int(float(rule) * runs * 1000) // 1000))
        raise CaseError(f"pass: {rule!r} is not 'all', 'k/n' or a rate between 0 and 1")


def _one(path: Path, data: dict) -> Case:
    where = f"{path}"
    if not isinstance(data, dict):
        raise CaseError(f"{where}: a case must be a mapping (key: value lines)")
    unknown = set(data) - KEYS
    if unknown:
        raise CaseError(f"{where}: unknown key(s) {sorted(unknown)}; allowed: {sorted(KEYS)}")
    if "id" not in data:
        raise CaseError(f"{where}: every case needs an id")
    where = f"{path} (case {data['id']})"
    if "message" in data:
        steps = [str(data["message"])]
    else:
        steps = []
        for s in data.get("steps") or []:
            if not isinstance(s, dict) or "say" not in s:
                raise CaseError(f"{where}: each step is a line like '- say: your message'")
            steps.append("" if s["say"] is None else str(s["say"]))
    variants = [str(v) for v in data.get("variants") or []]
    if variants and len(variants) < 2:
        raise CaseError(f"{where}: variants needs at least two messages")
    if not steps and not variants:
        raise CaseError(f"{where}: give message, steps or variants")
    checks = data.get("checks") or []
    for c in checks:
        if not isinstance(c, dict) or len(c) != 1:
            raise CaseError(f"{where}: each check is one line like '- contains: 45 days'")
        name = next(iter(c))
        if name not in CHECKS:
            raise CaseError(f"{where}: unknown check '{name}'; checks: {sorted(CHECKS)}")
        value = c[name]
        if name in ("no_error", "refuses") and not isinstance(value, bool):
            shown = f'the text "{value}"' if isinstance(value, str) else repr(value)
            raise CaseError(f"{where}: {name} must be true or false, not {shown} (write it without quotes)")
    if not checks:
        raise CaseError(f"{where}: a case needs at least one check")
    relation = data.get("relation", "same_results")
    if relation not in ("same_results", "all_pass"):
        raise CaseError(f"{where}: relation is same_results or all_pass")
    status = data.get("status", "active")
    if status not in ("active", "known-bug"):
        raise CaseError(f"{where}: status is active or known-bug")
    case = Case(id=str(data["id"]), title=str(data.get("title", data["id"])), file=path, steps=steps, checks=checks,
                customer=data.get("customer"), variants=variants, relation=relation, turn=data.get("turn"),
                runs=data.get("runs"), pass_rule=data.get("pass", "all"), status=status, bug=data.get("bug"),
                tags=list(data.get("tags") or []))
    case.required(5)  # checks the pass rule
    return case


def load(paths: list[str]) -> list[Case]:
    files: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(list(p.rglob("*.yaml")) + list(p.rglob("*.yml")))
        elif p.exists():
            files.append(p)
        else:
            raise CaseError(f"{p}: no such file or folder")
    cases: list[Case] = []
    for f in files:
        try:
            docs = list(yaml.safe_load_all(f.read_text(encoding="utf-8")))
        except yaml.YAMLError as e:
            raise CaseError(f"{f}: not valid YAML: {e}") from None
        for d in docs:
            if d is None:
                continue
            for item in d if isinstance(d, list) else [d]:
                cases.append(_one(f, item))
    seen = set()
    for c in cases:
        if c.id in seen:
            raise CaseError(f"case id {c.id} is used twice")
        seen.add(c.id)
    if not cases:
        raise CaseError("no cases found (files must end in .yaml or .yml)")
    return cases
