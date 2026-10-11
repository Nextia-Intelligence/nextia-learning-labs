"""ops drift: did the inputs (or the assistant's decisions) change? A reference period against a
current period.

    python -m ops drift REFERENCE_FILE CURRENT_FILE
    python -m ops drift FILE --at 30            the minutes before 30 against the minutes after
    python -m ops drift FILE --windows 500      every 500 tickets against the first 500

Inputs (data drift): the language of the message (a guess from common words), its length, the
channel. Outputs (prediction drift): the team, needs-a-person, the outcome. For each one: the
PSI (how much it moved) and a chi-square test (how sure we are that it moved). See ops/stats.py
for the method and the thresholds.

Drift says that the tickets changed. It does not say that the assistant is wrong: only the
agents' reviews can show that (python -m ops labels).
"""

from collections import Counter

from ops import stats
from ops.telemetry import Telemetry, table

INPUTS = ("ticket.language_guess", "ticket.message_chars", "ticket.channel")
OUTPUTS = ("team", "needs_human", "outcome")
PSI_LARGE, PSI_SMALL, P_LIMIT = 0.2, 0.1, 0.01


def register(commands) -> None:
    p = commands.add_parser("drift", help="input drift and prediction drift (PSI, chi-square)")
    p.add_argument("file", nargs="+", help="one file (with --at or --windows) or two files")
    p.add_argument("--at", type=float, help="split one file at this minute")
    p.add_argument("--windows", type=int, help="compare every N tickets with the first N")
    p.set_defaults(run=run)


def rows_of(tel: Telemetry, start: float | None = None, end: float | None = None) -> list[dict]:
    out = []
    for t in sorted(tel.tickets().values(), key=lambda t: t.get("received_time", 0)):
        if "received" not in t:
            continue
        minute = (t["received_time"] - tel.start) / 60
        if (start is not None and minute < start) or (end is not None and minute >= end):
            continue
        row = dict(t["received"])
        tri = t.get("triaged") or {}
        if tri.get("outcome") == "ok":
            row["team"], row["needs_human"] = tri.get("team"), tri.get("needs_human")
        if tri:
            row["outcome"] = tri.get("outcome")
        out.append(row)
    return out


def compare(ref: list[dict], cur: list[dict], feature: str) -> dict:
    if feature == "ticket.message_chars":
        rv = [r[feature] for r in ref if feature in r]
        cv = [r[feature] for r in cur if feature in r]
        if not rv or not cv:
            return {}
        edges = stats.quantile_edges(rv)
        rc, cc = stats.binned(rv, edges), stats.binned(cv, edges)
        detail = f"median {sorted(rv)[len(rv) // 2]} -> {sorted(cv)[len(cv) // 2]} characters"
    else:
        rc = Counter(str(r[feature]) for r in ref if r.get(feature) is not None)
        cc = Counter(str(r[feature]) for r in cur if r.get(feature) is not None)
        if not rc or not cc:
            return {}
        top = sorted(set(rc) | set(cc), key=lambda k: -(rc[k] + cc[k]))[:3]
        detail = ", ".join(
            f"{k} {rc[k] / sum(rc.values()):.0%} -> {cc[k] / sum(cc.values()):.0%}" for k in top
        )
    value = stats.psi(rc, cc)
    chi, df, p = stats.chi_square(rc, cc)
    verdict = (
        "LARGE change"
        if value >= PSI_LARGE
        else ("small change" if value >= PSI_SMALL else "no real change")
    )
    if p >= P_LIMIT and value >= PSI_SMALL:
        verdict += " (not sure: p >= 0.01)"
    return {
        "feature": feature,
        "psi": value,
        "chi2": chi,
        "df": df,
        "p": p,
        "verdict": verdict,
        "detail": detail,
        "n": (sum(rc.values()), sum(cc.values())),
    }


def report(ref: list[dict], cur: list[dict]) -> list[dict]:
    return [r for f in INPUTS + OUTPUTS if (r := compare(ref, cur, f))]


def print_report(results: list[dict], ref_label: str, cur_label: str) -> None:
    print(f"Reference: {ref_label}. Current: {cur_label}.")
    rows = []
    for r in results:
        kind = "input" if r["feature"] in INPUTS else "output"
        rows.append(
            [
                kind,
                r["feature"].removeprefix("ticket."),
                f"{r['psi']:.3f}",
                f"{r['p']:.3g}",
                r["verdict"],
                r["detail"],
            ]
        )
    print(table(rows, ["kind", "feature", "PSI", "p-value", "verdict", "reference -> current"]))
    print(
        "PSI: < 0.1 no real change, 0.1-0.2 small, > 0.2 large (a rule of thumb). p-value: "
        "chi-square test; < 0.01 = the difference is unlikely to be chance."
    )
    print("Drift is not an error rate: compare the agents' reviews (python -m ops labels).")


def run(args) -> int:
    if len(args.file) == 2 and args.at is None and args.windows is None:
        ref_t, cur_t = Telemetry.load(args.file[0]), Telemetry.load(args.file[1])
        ref, cur = rows_of(ref_t), rows_of(cur_t)
        print_report(
            report(ref, cur),
            f"{args.file[0]} ({len(ref):,} tickets)",
            f"{args.file[1]} ({len(cur):,} tickets)",
        )
        return 0
    tel = Telemetry.load(*args.file)
    if args.at is not None:
        ref, cur = rows_of(tel, end=args.at), rows_of(tel, start=args.at)
        print_report(
            report(ref, cur),
            f"before minute {args.at:g} ({len(ref):,} tickets)",
            f"from minute {args.at:g} ({len(cur):,} tickets)",
        )
        return 0
    if args.windows:
        rows = rows_of(tel)
        n = args.windows
        windows = [rows[i : i + n] for i in range(0, len(rows) - n + 1, n)]
        if len(windows) < 2:
            raise ValueError(f"fewer than two windows of {n} tickets")
        out = []
        for i, w in enumerate(windows):
            lang = compare(windows[0], w, "ticket.language_guess")
            team = compare(windows[0], w, "team")
            fr = sum(r.get("ticket.language_guess") == "fr" for r in w) / len(w)
            out.append(
                [
                    f"{i * n + 1}-{(i + 1) * n}",
                    f"{fr:.1%}",
                    f"{lang['psi']:.3f}",
                    f"{lang['p']:.2g}",
                    f"{team['psi']:.3f}" if team else "-",
                ]
            )
        print(f"Each window of {n} tickets against the first window:")
        print(table(out, ["tickets", "French (guess)", "PSI language", "p", "PSI team"]))
        return 0
    raise ValueError("give two files, or one file with --at or --windows")
