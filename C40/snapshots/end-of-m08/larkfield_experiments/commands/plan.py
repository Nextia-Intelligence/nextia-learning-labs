"""xp plan: write a one-page test plan before the test starts, and check that it is complete."""

import re
from datetime import date
from pathlib import Path

NAME = "plan"
HELP = "write a test plan template (xp plan new NAME) or check a plan (xp plan check FILE)"

FIELDS = ["Hypothesis", "Unit", "Primary metric", "Guardrail metrics", "Minimum detectable effect", "Sample size",
          "Duration", "Stopping rule", "Decision if B is better", "Decision if B is worse", "Decision if no clear effect"]

TEMPLATE = """# Test plan: {name}

Written on {today}, before the test starts. Change it only with a dated note that says why.

{fields}
## Checks before reading the result

- Sample ratio: the share of customers in B is 50% (chi-square test, p > 0.001).
- The test ran for the planned number of full weeks.
"""


def add(p):
    p.add_argument("action", choices=["new", "check"])
    p.add_argument("name", help="the test's name (new) or the plan file (check)")


def run(args):
    if args.action == "new":
        path = Path("plans") / f"{args.name}.md"
        if path.exists():
            raise SystemExit(f"{path} exists. A plan is written once: add a dated note instead of a new plan.")
        path.parent.mkdir(exist_ok=True)
        fields = "".join(f"- **{f}:** TODO\n" for f in FIELDS)
        path.write_text(TEMPLATE.format(name=args.name, today=date.today().isoformat(), fields=fields))
        print(f"Wrote {path}. Fill in every TODO before the test starts, then: xp plan check {path}")
        return
    text = Path(args.name).read_text()
    missing = [f for f in FIELDS if not re.search(rf"\*\*{re.escape(f)}:\*\*\s*(?!TODO)\S", text)]
    if missing:
        print(f"Not ready: {len(missing)} of {len(FIELDS)} fields are missing or TODO: {', '.join(missing)}.")
        raise SystemExit(1)
    print(f"Ready: all {len(FIELDS)} fields are filled in.")
