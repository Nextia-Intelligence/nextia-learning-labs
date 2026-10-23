"""Policy as code: commands of python -m estate."""

import json
import sys



def cmd_policy(a):
    from estate import policy

    pol = policy.load(a.file)
    if a.action == "check":
        problems = policy.check_policy(pol)
        print("\n".join(problems) or "The policy is valid.")
        sys.exit(1 if problems else 0)
    if a.action == "test":
        results = policy.run_tests(pol, a.cases)
        for name, ok, got in results:
            print(f"{'pass' if ok else 'FAIL'}  {name}\n      {got}")
        failed = sum(1 for r in results if not r[1])
        print(f"{len(results) - failed} passed, {failed} failed")
        sys.exit(1 if failed else 0)
    d = policy.decide(pol, a.tool, json.loads(a.arguments or "{}"), a.kind)
    print(d.text())
    if a.approver:
        print(policy.may_approve(pol, d, a.approver)[1])


ORDER = 31


def register(sub) -> dict:
    p = sub.add_parser("policy", help="check, test or explain the approval policy")
    p.add_argument("action", choices=["check", "test", "explain"])
    p.add_argument("--file")
    p.add_argument("--cases")
    p.add_argument("--tool", default="")
    p.add_argument("--arguments")
    p.add_argument("--kind", default="write")
    p.add_argument("--approver")
    return {"policy": cmd_policy}
