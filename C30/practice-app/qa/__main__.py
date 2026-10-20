"""python -m qa run CASES... [--runs N] [--seed-start S] [--app FOLDER] [--report-dir DIR] [--judge recorded|live]"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import RUNNER_VERSION
from .cases import CaseError, load
from .runner import Runner, save_exports

LABEL = {"pass": "PASS", "fail": "FAIL", "not_run": "NOT RUN"}


def _label(r: dict) -> str:
    if r["status"] == "known-bug":
        return {"pass": "FIXED?", "fail": "KNOWN", "not_run": "NOT RUN"}[r["result"]]
    return LABEL[r["result"]]


def cmd_run(args) -> int:
    try:
        cases = load(args.cases)
    except CaseError as e:
        print(f"Case error: {e}", file=sys.stderr)
        return 2
    runner = Runner(Path(args.app) if args.app else None, "live" if args.live else "sim", args.judge)
    v = runner.versions()
    print(f"QA run: {len(cases)} case(s) from {' '.join(args.cases)}")
    print(f"App: {v['app']} {v['app_version']} | model {v['model']} | prompt {v['prompt_version']}")
    results = []
    width = max(len(c.id) for c in cases)
    for case in cases:
        runs = args.runs if args.runs_override or not case.runs else case.runs
        r = runner.run_case(case, runs, args.seed_start)
        results.append(r)
        seeds = f"seeds {args.seed_start}-{args.seed_start + runs - 1}" if runs > 1 else f"seed {args.seed_start}"
        extra = f"  known bug {case.bug}" if case.status == "known-bug" and case.bug else ""
        print(f"{_label(r):8}{case.id:<{width}}  {r['passed_runs']}/{runs} passed (needs {r['required']}; "
              f"{seeds}){extra}")
        if r["result"] != "pass" or args.verbose:
            shown = [x for x in r["run_results"] if x["passed"] is not True][: 1 if not args.verbose else None]
            for x in shown:
                print(f"        {'failing run' if args.verbose else 'first failing run'}: seed {x['seed']}, trace {x['trace_id']}")
                for f in x["failures"][:4]:
                    print(f"          - {f}")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.report_dir) / f"qa-{stamp}"
    exports = {r["id"]: save_exports(r, out / "conversations") for r in results}
    for r in results:
        for x in r["run_results"]:
            x.pop("export", None)
    counts = {k: sum(1 for r in results if _label(r) == k) for k in ("PASS", "FAIL", "KNOWN", "FIXED?", "NOT RUN")}
    report = {"runner_version": RUNNER_VERSION, "started": stamp, "versions": v, "seed_start": args.seed_start,
              "judge": args.judge, "summary": counts, "cases": results, "conversations": exports}
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "report.md").write_text(markdown(report), encoding="utf-8")
    print()
    print(f"{len(results)} case(s): {counts['PASS']} passed, {counts['FAIL']} failed, {counts['KNOWN']} known bug(s) "
          f"still failing, {counts['FIXED?']} known bug(s) now passing, {counts['NOT RUN']} not run")
    print(f"Report: {out / 'report.md'}")
    return 1 if counts["FAIL"] else 0


def markdown(rep: dict) -> str:
    v = rep["versions"]
    lines = [f"# QA run {rep['started']}", "",
             f"- App: {v['app']} {v['app_version']}, model {v['model']}, prompt {v['prompt_version']}",
             f"- Runner {rep['runner_version']}, first seed {rep['seed_start']}, judge {rep['judge']}",
             f"- Summary: {rep['summary']}", "",
             "| Result | Case | Passed runs | Needs | Bug |", "|---|---|---|---|---|"]
    for r in rep["cases"]:
        lines.append(f"| {_label(r)} | {r['id']} | {r['passed_runs']}/{r['runs']} | {r['required']} | "
                     f"{r.get('bug') or ''} |")
    for r in rep["cases"]:
        bad = [x for x in r["run_results"] if x["passed"] is not True]
        if not bad:
            continue
        lines += ["", f"## {r['id']}: {r['title']}", ""]
        for x in bad:
            lines.append(f"- Seed {x['seed']}, trace {x['trace_id']}: " + "; ".join(x["failures"]))
            reply = (x["reply"] or "").replace("\n", " ")
            lines.append(f"  - Reply: {reply[:300]}")
        for p in rep["conversations"].get(r["id"], [])[:3]:
            lines.append(f"- Conversation: `{p}`")
    return "\n".join(lines) + "\n"


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m qa", description="Run YAML test cases against the help desk app.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run cases")
    r.add_argument("cases", nargs="+", help="case files or folders")
    r.add_argument("--runs", type=int, default=5, help="runs per case (default 5; a case's runs: wins)")
    r.add_argument("--runs-override", action="store_true", help="use --runs also for cases that set runs:")
    r.add_argument("--seed-start", type=int, default=1, help="seed of the first run (default 1)")
    r.add_argument("--app", help="folder of the app version to test (default: this folder)")
    r.add_argument("--report-dir", default="reports")
    r.add_argument("--judge", choices=["recorded", "live"], default="recorded")
    r.add_argument("--live", action="store_true", help="run the app in live mode (real model, your key)")
    r.add_argument("-v", "--verbose", action="store_true", help="show every failing run")
    r.set_defaults(fn=cmd_run)
    c = sub.add_parser("check", help="check that case files are valid, without running them")
    c.add_argument("cases", nargs="+")
    c.set_defaults(fn=cmd_check)
    args = p.parse_args(argv)
    sys.exit(args.fn(args))


def cmd_check(args) -> int:
    try:
        cases = load(args.cases)
    except CaseError as e:
        print(f"Case error: {e}", file=sys.stderr)
        return 2
    print(f"{len(cases)} valid case(s): " + ", ".join(c.id for c in cases))
    return 0


if __name__ == "__main__":
    main()
