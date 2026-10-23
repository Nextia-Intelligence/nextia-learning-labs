"""A runaway agent, caused on purpose: one app sends the same recorded request again and again through the
gateway. Which limit stops it, and what did it cost before the stop?

    python -m apps.runaway support-workflow --attempts 300              a new run ID for every call
    python -m apps.runaway support-workflow --attempts 300 --same-run   one run that never ends

The request is real: the first recorded step of one unit of the app's work (for the support workflow, ticket
T-90103, step 1 on strong-reasoning: the request of the course's measured runaway). The loop is constructed: it
is the bug of a bad deployment, not anything that an earlier course recorded. The calls go through the gateway
with the app's own token, as fast as the gateway answers, on the real clock: a rate limit counts this minute,
and a quota counts today. The gateway counts requests per calendar minute (12:04:00 to 12:04:59), so the
loop waits for the next minute to start (--now starts at once): then your counts match the lesson's.
"""

import argparse
import time
from collections import Counter

from apps.replay import APPS, request_for, units

FIRST = {"support-workflow": ("T-90103", 1)}     # the measured runaway's ticket and recorded repeat


def the_request(app: str):
    """The unit and the first recorded request (endpoint, body) that the loop sends again and again."""
    all_units = units(app)
    group, repeat = FIRST.get(app, (all_units[0].group, all_units[0].repeat))
    unit = next(u for u in all_units if u.group == group and u.repeat == repeat)
    return unit, request_for(app, unit.rows[0], "gateway")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m apps.runaway")
    ap.add_argument("app", choices=list(APPS))
    ap.add_argument("--attempts", type=int, default=300)
    ap.add_argument("--same-run", action="store_true", help="send every call with the same run ID")
    ap.add_argument("--now", action="store_true", help="start at once, not at the next minute")
    a = ap.parse_args(argv)
    from apps.client import Sender

    unit, (path, body) = the_request(a.app)
    sender = Sender(a.app, "gateway")
    how = "one run ID for every call" if a.same_run else "a new run ID for every call"
    print(f"{a.app}: {a.attempts} attempts of {unit.group.split('|')[0]} step 1 ({body['model']}) through the gateway, "
          f"{how}")
    if not a.now:
        wait = 60 - time.time() % 60
        print(f"Waiting {wait:.0f} s for the next minute to start (--now starts at once)", flush=True)
        time.sleep(wait)
    counts, cost, first, warning = Counter(), 0.0, {}, None
    started = time.monotonic()
    run = f"runaway-{int(time.time())}"
    for i in range(a.attempts):
        run_id = run if a.same_run else f"{run}-{i}"
        r = sender.send(path, body, extra_headers={"x-run-id": run_id, "x-sim-repeat": str(unit.repeat)})
        if r.status_code == 200:
            counts["answered"] += 1
            cost += float(r.headers.get("x-gateway-cost-usd") or 0)
            if warning is None and r.headers.get("x-gateway-budget-warning"):
                warning = (counts["answered"], r.headers["x-gateway-budget-warning"])
            continue
        err = (r.json().get("error") or {}) if r.headers.get("content-type", "").startswith("application/json") else {}
        code = err.get("code") or str(r.status_code)
        counts[code] += 1
        if code not in first:
            first[code] = (counts["answered"], cost, time.monotonic() - started, r.status_code, err.get("message", ""),
                           r.headers.get("retry-after"))
    seconds = time.monotonic() - started
    print(f"answered {counts['answered']} | cost US${cost:.4f} | {seconds:.1f} s")
    refused = {k: v for k, v in counts.items() if k != "answered"}
    if refused:
        print("refused " + ", ".join(f"{k} {v}" for k, v in refused.items()))
    if warning:
        print(f"budget warning from answer {warning[0]}: {warning[1]}")
    for code, (n, c, s, status, message, retry) in first.items():
        print(f"first {code}: after {n} answers and US${c:.4f} ({s:.1f} s): {status} {message}"
              + (f" (retry-after: {retry} s)" if retry else ""))


if __name__ == "__main__":
    main()
