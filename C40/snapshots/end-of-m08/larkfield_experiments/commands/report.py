"""xp report: a one-page result report from a run's analysis, its SRM check and its guardrails."""

import re
from pathlib import Path

from ..commands.analyse import estimate
from ..commands.srm import srm_test
from ..metrics import split
from ..runs import load_run
from ..stats import diff_ratio

NAME = "report"
HELP = "write a one-page result report (Markdown) for an A/B run: decision, effect and range, checks, limits"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--cuped", action="store_true")
    p.add_argument("--plan", help="the test plan written before the test: the report compares its metrics and duration")
    p.add_argument("--out", help="the report file (default: reports/<run>.md)")


def units(run_):
    """The run's randomisation units (one row each) and the function that estimates a metric on them."""
    tables = run_.meta["tables"]
    if "tickets" in tables and "customers" not in tables:  # the prompt test: tickets, grouped by customer
        from ..commands.prompt import per_customer

        def per_ticket(df, metric, cuped=False):
            if cuped:
                raise SystemExit("--cuped needs each customer's spending before the test. This run has none.")
            a, b = split(df)
            return diff_ratio(a[metric], a["tickets"], b[metric], b["tickets"])
        return per_customer(run_.table("tickets")), per_ticket
    return run_.table(run_.meta.get("analysis_table", "customers")), estimate


def decide(primary, guardrails):
    if primary["low"] > 0 and not any(g["low"] > 0 for g in guardrails.values()):
        return "Ship B", "B is better on the primary metric, and no guardrail is clearly worse."
    if primary["low"] > 0:
        return "Discuss before shipping", "B is better on the primary metric, but a guardrail is clearly worse."
    if primary["high"] < 0:
        return "Keep A", "B is worse on the primary metric."
    return "No clear effect: keep A", (f"The effect is between {primary['low']:+.3f} and {primary['high']:+.3f}: the "
                                       "test cannot tell a small gain from a small loss. It does rule out effects "
                                       "outside this range.")


def plan_checks(meta, plan):
    """The report's lines on the duration and the metrics: compared with the plan if there is one, else a reminder."""
    days = f"{meta.get('days')} days, {meta.get('start')} to {meta.get('end')}"
    metrics = [meta["primary_metric"]] + list(meta.get("guardrails", []))
    if not plan:
        return [f"- Duration: {days}. Not compared with a plan: give the plan with --plan, or check it yourself.",
                f"- Metrics: {', '.join(metrics)} (the run's own). Check that the plan chose them before the test."]
    path = Path(plan)
    if not path.exists():
        raise SystemExit(f"No plan file {plan}. Give the plan written before the test, or leave out --plan.")
    text = path.read_text()

    def field(name):
        m = re.search(rf"\*\*{re.escape(name)}:\*\*\s*(.*)", text)
        return m.group(1).strip() if m and not m.group(1).strip().startswith("TODO") else ""

    def named(metric, words):  # "return_rate" or "return rate"
        return any(re.search(rf"\b{re.escape(m)}\b", words, re.I) for m in {metric, metric.replace("_", " ")})

    lines = []
    duration = field("Duration")
    found = re.search(r"(\d+)\s*(day|week)", duration, re.I)
    if found:
        planned = int(found.group(1)) * (7 if found.group(2).lower() == "week" else 1)
        same = planned == meta.get("days")
        lines.append(f"- Duration: {days}" + (", as in the plan." if same else
                     f". The plan says {planned} days: explain the difference."))
    else:
        lines.append(f"- Duration: {days}. The plan gives no number of days or weeks: check it yourself.")
    primary, guards = field("Primary metric"), field("Guardrail metrics")
    lines.append(f"- Primary metric: {metrics[0]}, " + ("as in the plan." if named(metrics[0], primary) else
                 f"but the plan says \"{primary or 'nothing'}\": report the plan's metric, or explain the change."))
    for g in metrics[1:]:
        lines.append(f"- Guardrail: {g}, " + ("as in the plan." if named(g, guards) else "NOT in the plan's guardrails."))
    return lines + [f"- Plan: {plan}. The tool compares names and days only: check that the plan was written "
                    "before the test."]


def run(args):
    run_ = load_run(args.run)
    meta = run_.meta
    df, est = units(run_)
    na, nb = int((df.variant == "A").sum()), int((df.variant == "B").sum())
    _, p_srm = srm_test(na, nb, meta.get("split", 0.5))
    primary = est(df, meta["primary_metric"], args.cuped)
    guards = {g: est(df, g) for g in meta.get("guardrails", [])}
    if p_srm < 0.001:
        decision, why = "Do not use this result", f"Sample ratio mismatch (p = {p_srm:.2g}): find the cause, then test again."
    else:
        decision, why = decide(primary, guards)
    checks = plan_checks(meta, args.plan)
    lines = [f"# Result: {meta['about']}", "",
             f"**Decision: {decision}.** {why}", "",
             "## The effect", "",
             f"- {meta['primary_metric']} (primary): A {primary['mean_a']:.4f}, B {primary['mean_b']:.4f}; difference "
             f"{primary['difference']:+.4f} ({primary['relative']:+.1%}), 95% interval {primary['low']:+.4f} to "
             f"{primary['high']:+.4f} ({primary['method']})."]
    for g, r in guards.items():
        lines.append(f"- {g} (guardrail): difference {r['difference']:+.4f}, 95% interval {r['low']:+.4f} to {r['high']:+.4f}.")
    lines += ["", "## Checks", "",
              f"- Split: A {na:,}, B {nb:,} customers; sample ratio test p = {p_srm:.3g}.", *checks, "",
              "## Limits", "",
              "- The effect is for the customers and the weeks of the test. A season or a new customer mix can change it.",
              "- Synthetic data from the course simulator.", ""]
    out = Path(args.out or f"reports/{run_.folder.name}.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"Decision: {decision}. Wrote {out}.")
