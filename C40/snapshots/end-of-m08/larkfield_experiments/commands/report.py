"""xp report: a one-page result report from a run's analysis, its SRM check and its guardrails."""

from pathlib import Path

from ..commands.analyse import estimate
from ..commands.srm import srm_test
from ..runs import load_run

NAME = "report"
HELP = "write a one-page result report (Markdown) for an A/B run: decision, effect and range, checks, limits"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--cuped", action="store_true")
    p.add_argument("--out", help="the report file (default: reports/<run>.md)")


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


def run(args):
    run_ = load_run(args.run)
    meta, df = run_.meta, run_.table("customers")
    na, nb = int((df.variant == "A").sum()), int((df.variant == "B").sum())
    _, p_srm = srm_test(na, nb, meta.get("split", 0.5))
    primary = estimate(df, meta["primary_metric"], args.cuped)
    guards = {g: estimate(df, g) for g in meta.get("guardrails", [])}
    if p_srm < 0.001:
        decision, why = "Do not use this result", f"Sample ratio mismatch (p = {p_srm:.2g}): find the cause, then test again."
    else:
        decision, why = decide(primary, guards)
    lines = [f"# Result: {meta['about']}", "",
             f"**Decision: {decision}.** {why}", "",
             "## The effect", "",
             f"- {meta['primary_metric']} (primary): A {primary['mean_a']:.4f}, B {primary['mean_b']:.4f}; difference "
             f"{primary['difference']:+.4f} ({primary['relative']:+.1%}), 95% interval {primary['low']:+.4f} to "
             f"{primary['high']:+.4f} ({primary['method']})."]
    for g, r in guards.items():
        lines.append(f"- {g} (guardrail): difference {r['difference']:+.4f}, 95% interval {r['low']:+.4f} to {r['high']:+.4f}.")
    lines += ["", "## Checks", "",
              f"- Split: A {na:,}, B {nb:,} customers; sample ratio test p = {p_srm:.3g}.",
              f"- Duration: {meta.get('days')} days, {meta.get('start')} to {meta.get('end')}, as planned.",
              "- The primary metric and the guardrails were chosen in the test plan before the test.", "",
              "## Limits", "",
              "- The effect is for the customers and the weeks of the test. A season or a new customer mix can change it.",
              "- Synthetic data from the course simulator.", ""]
    out = Path(args.out or f"reports/{run_.folder.name}.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"Decision: {decision}. Wrote {out}.")
