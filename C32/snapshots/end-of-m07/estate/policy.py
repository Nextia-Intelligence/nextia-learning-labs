"""Policy as code: which actions need a person's approval, and whose (config/policy/approvals.yaml).

The policy is data, read by code that runs outside the model: the control plane checks it before it signs
an approval grant, and the tool gateway checks it again before it lets a write through. `run_tests()` runs
the policy's own test cases (config/policy/approvals-tests.yaml): change a rule, run the tests, as with code.
"""

from dataclasses import dataclass

import yaml

from estate import paths, registry


@dataclass(frozen=True)
class Decision:
    tool: str
    rule: str                 # the rule that decided ("reads", "default")
    denied: bool = False
    needs: str | None = None  # the lowest role that may approve; None: no approval needed

    def text(self) -> str:
        if self.denied:
            return f"{self.tool}: refused (rule {self.rule})"
        return f"{self.tool}: " + (f"needs approval by {self.needs} or above" if self.needs else "no approval needed") \
            + f" (rule {self.rule})"


def load(path=None) -> dict:
    return yaml.safe_load(open(path or paths.CONFIG / "policy" / "approvals.yaml", encoding="utf-8").read())


def check_policy(policy: dict) -> list[str]:
    problems = []
    roles = policy.get("roles") or []
    ids = set()
    for r in policy.get("rules") or []:
        if r.get("id") in ids:
            problems.append(f"rule {r.get('id')}: the ID is used twice")
        ids.add(r.get("id"))
        if r.get("approve_by") not in (*roles, "none"):
            problems.append(f"rule {r.get('id')}: approve_by must be one of {', '.join(roles)} or none")
        if not (r.get("match") or {}).get("tool"):
            problems.append(f"rule {r.get('id')}: match.tool is missing")
    if policy.get("default") not in ("deny", "allow"):
        problems.append("default: deny or allow")
    return problems


def _matches(match: dict, tool: str, arguments: dict, data_class: str | None) -> bool:
    tools = match.get("tool")
    if isinstance(tools, str):
        tools = [tools]
    if tool not in tools:
        return False
    amount = arguments.get("amount")
    if "amount_at_most" in match and (amount is None or float(amount) > float(match["amount_at_most"])):
        return False
    if "amount_above" in match and (amount is None or float(amount) <= float(match["amount_above"])):
        return False
    if "data_class" in match:
        classes = match["data_class"] if isinstance(match["data_class"], list) else [match["data_class"]]
        if data_class not in classes:
            return False
    return True


def decide(policy: dict, tool: str, arguments: dict, kind: str = "write", data_class: str | None = None) -> Decision:
    """What the policy says about one action. Reads are allowed when the policy says `reads: allow`."""
    if kind == "read" and policy.get("reads") == "allow":
        return Decision(tool, "reads")
    for r in policy.get("rules") or []:
        if _matches(r.get("match") or {}, tool, arguments or {}, data_class):
            by = r.get("approve_by")
            return Decision(tool, r["id"], needs=None if by == "none" else by)
    if policy.get("default") == "allow":
        return Decision(tool, "default")
    return Decision(tool, "default", denied=True)


def role_rank(policy: dict, role: str | None) -> int:
    roles = policy.get("roles") or []
    return roles.index(role) if role in roles else -1


def may_approve(policy: dict, decision: Decision, user_id: str, people: dict | None = None) -> tuple[bool, str]:
    """Whether a person may approve this decision, and why not. The role comes from config/people.yaml, never
    from the person's own claim."""
    people = people or registry.people()
    person = people.get(user_id)
    if decision.denied:
        return False, f"the policy refuses {decision.tool} (rule {decision.rule})"
    if decision.needs is None:
        return True, "no approval needed"
    if person is None:
        return False, f"{user_id} is not a person in config/people.yaml"
    if person.get("left"):
        return False, f"{user_id} left the company on {person['left']}"
    if role_rank(policy, person.get("approves")) < role_rank(policy, decision.needs):
        return False, f"{person['name']} may not approve this: it needs a {decision.needs.replace('_', ' ')} or above " \
                      f"(rule {decision.rule})"
    return True, f"{person['name']} ({person['approves'].replace('_', ' ')}) may approve it (rule {decision.rule})"


def run_tests(policy: dict | None = None, cases_path=None) -> list[tuple[str, bool, str]]:
    """Runs the policy's test cases: (name, passed, what happened)."""
    policy = policy or load()
    cases = yaml.safe_load(open(cases_path or paths.CONFIG / "policy" / "approvals-tests.yaml",
                                encoding="utf-8").read())["cases"]
    out = []
    for c in cases:
        a = c["action"]
        d = decide(policy, a["tool"], a.get("arguments") or {}, c.get("kind", "write"), a.get("data_class"))
        exp = c["expect"]
        ok, got = True, d.text()
        if "denied" in exp:
            ok &= d.denied == exp["denied"]
        if "needs" in exp:
            ok &= (d.needs or "none") == exp["needs"]
        if "approved" in exp:
            allowed, why = may_approve(policy, d, c.get("approver", ""))
            ok &= allowed == exp["approved"]
            got += f"; {c.get('approver')}: {why}"
        out.append((c["name"], ok, got))
    return out
