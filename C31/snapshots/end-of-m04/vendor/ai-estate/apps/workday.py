"""A replayed day of the support workflow through both gateways, for a kill-switch drill.

    python -m apps.workday                          the day's 14 tickets, in order
    python -m apps.workday --tasks 1-4              only tasks 1 to 4 (use a switch, then go on with --tasks 5-7)
    python -m apps.workday --tasks 8 --no-approve   run task 8 and leave it waiting for its approval
    python -m apps.workday --approve RUN_ID         approve a waiting run later (for example after a drain)

For each task it runs the agents course's workflow, `python -m resolver run <ticket> --variant agent_structured
--model strong-reasoning`, with RESOLVER_PROVIDER=gateway and RESOLVER_TOOLS=gateway. When the run proposes
changes, it approves them with `python -m resolver approve <run> --as <role> --approver <person>`: the tool plays
the person whose role the run needs (Sam for an agent's approval, Camille for a team lead's, Grace above).
It prints one line per task. The tickets are the agents course's practice tasks; the model's answers are its
recordings, replayed by the provider simulator. The people's approvals are a practice shortcut.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
TASKS = ["T-90103", "T-90104", "T-90603", "T-65273", "T-64872", "T-90201", "T-90101", "T-90205", "T-90102",
         "T-90408", "T-90106", "T-90701", "T-90203", "T-90604"]
PERSON = {"agent": "usr-sam", "team_lead": "usr-camille", "grace": "usr-grace"}


def resolver(*args: str) -> str:
    env = {**os.environ, "RESOLVER_PROVIDER": "gateway", "RESOLVER_TOOLS": "gateway"}
    r = subprocess.run([sys.executable, "-m", "resolver", *args], cwd=PROJECT, env=env, capture_output=True,
                       text=True)
    return (r.stdout + r.stderr).strip()


def selection(text: str) -> list[int]:
    """'1-4' or '8' or '5-7,9': task numbers from 1 to 14."""
    out = []
    for part in text.split(","):
        a, _, b = part.strip().partition("-")
        out += range(int(a), int(b or a) + 1)
    if not out or min(out) < 1 or max(out) > len(TASKS):
        raise SystemExit(f"--tasks: numbers from 1 to {len(TASKS)}, for example 1-4")
    return out


def approve(run_id: str, role: str) -> str:
    person = PERSON.get(role, "usr-grace")
    out = resolver("approve", run_id, "--as", role, "--approver", person)
    lines = out.splitlines()
    status = next((x.split(": ", 1)[1] for x in lines if x.startswith("Status: ")), "")
    if not status:        # the platform refused the approval: nothing changed, the run still waits
        return f"approval by {person} refused: {lines[-1] if lines else out}"
    done = [re.sub(r" \(operation \w+, \d+ call\(s\)\)", "", x) for x in lines
            if re.match(r"^\w+ LK-\d+: (done|failed)", x)]
    return f"approved by {person}: " + "; ".join(done) + f" | {status}"


def run(n: int, approve_it: bool = True) -> None:
    ticket = TASKS[n - 1]
    out = resolver("run", ticket, "--variant", "agent_structured", "--model", "strong-reasoning")
    lines = out.splitlines()
    first = lines[1] if len(lines) > 1 else out
    outcome = re.sub(r" \| \d+ model call.*$", "", first.removeprefix("Outcome: "))
    m = re.search(r"approve (\S+) --as (\w+)", out)
    if m and approve_it:
        tail = approve(m.group(1), m.group(2))
    elif m:
        tail = (f"waiting: python -m apps.workday --approve {m.group(1)}"
                f"   (needs {m.group(2).replace('_', ' ')} or above)")
    else:
        last = next((x for x in reversed(lines) if x.startswith("Last error: ")), "")
        tail = last or "no change proposed"
    print(f"task {n:>2}  {ticket}  {outcome} | {tail}", flush=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m apps.workday", description=__doc__.splitlines()[0])
    ap.add_argument("--tasks", default=f"1-{len(TASKS)}", help="which tasks of the day, for example 1-4 or 8")
    ap.add_argument("--no-approve", action="store_true", help="leave the proposals waiting for an approval")
    ap.add_argument("--approve", metavar="RUN_ID", help="approve one waiting run (the person its role needs)")
    a = ap.parse_args(argv)
    if a.approve:
        from resolver.approval import required_role
        from resolver.checkpoint import CheckpointStore

        try:
            state = CheckpointStore().load(a.approve)
        except Exception:
            state = None
        if state is None or state.status != "waiting_approval":
            raise SystemExit(f"{a.approve}: no run waits for an approval with this ID (python -m resolver runs)")
        n = TASKS.index(state.task_id) + 1 if state.task_id in TASKS else 0
        print(f"task {n:>2}  {state.task_id}  {approve(a.approve, required_role(state))}", flush=True)
        return
    for n in selection(a.tasks):
        run(n, not a.no_approve)


if __name__ == "__main__":
    main()
