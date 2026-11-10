"""xp srm: check the split before the result. A sample ratio mismatch (SRM) means the groups are not what the
coin flip made, and the result must not be used."""

from scipy.stats import chisquare

from ..runs import load_run

NAME = "srm"
HELP = "check for a sample ratio mismatch (chi-square test of the customers per group), overall and --by a column"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--by", help="also check each segment of this column, e.g. device, to find where it breaks")


def srm_test(counts_a, counts_b, share_b=0.5):
    total = counts_a + counts_b
    stat, p = chisquare([counts_a, counts_b], [total * (1 - share_b), total * share_b])
    return float(stat), float(p)


def run(args):
    run_ = load_run(args.run)
    df = run_.table("customers")
    share = run_.meta.get("split", 0.5)
    na, nb = int((df["variant"] == "A").sum()), int((df["variant"] == "B").sum())
    stat, p = srm_test(na, nb, share)
    verdict = "SAMPLE RATIO MISMATCH: do not use this result; find the cause first." if p < 0.001 else "no mismatch."
    print(f"Run {run_.folder.name}: A {na:,}, B {nb:,} customers; B is {nb / (na + nb):.2%} (planned {share:.0%}).")
    print(f"  chi-square {stat:.1f}, p = {p:.3g}: {verdict}")
    segments = {}
    if args.by:
        for value, part in df.groupby(args.by):
            a, b = int((part["variant"] == "A").sum()), int((part["variant"] == "B").sum())
            s, ps = srm_test(a, b, share)
            segments[str(value)] = {"a": a, "b": b, "p": ps}
            print(f"  {args.by} = {value}: A {a:,}, B {b:,} (B {b / (a + b):.2%}), p = {ps:.3g}")
    run_.save_analysis({"command": NAME, "a": na, "b": nb, "p": p, "mismatch": p < 0.001, "segments": segments})


def check(analysis, truth):
    planted = truth.get("planted")
    lines = [f"Your check: {'a mismatch' if analysis['mismatch'] else 'no mismatch'} (p = {analysis['p']:.3g})."]
    lines.append(f"The simulator: {planted}" if planted else "The simulator: this run has no planted problem in the "
                 "split. (With p < 0.001 as the rule, about 1 run in 1,000 shows a mismatch by chance.)")
    return lines
