"""An hour of the estate's traffic, compressed: the triage service, the support workflow and the document
assistant send their real recorded requests through the gateway, about 2 a second, for --seconds.

    python -m apps.traffic --seconds 150

Every 10 seconds it prints one line: what each app got back (answered, answered with the gateway's "degraded"
mark, or the refusal's code) and which replicas answered. Run it in one terminal, and stop a replica or the
control plane in a second terminal (python -m estate down replica-b, python -m estate down control). The mix
follows Larkfield's day (822 tickets, 45 workflow runs and 40 questions), with more questions than usual so
that every risk tier shows up. A unit stops at its first refusal: the app hands that work to a person.
"""

import argparse
import random
import time
from collections import Counter

import httpx

from apps.replay import request_for, units

APPS = {"ticket-triage": ("triage", 822), "support-workflow": ("workflow", 45), "doc-assistant": ("documents", 120)}


def label(r: httpx.Response) -> str:
    if r.status_code == 200:
        return "degraded" if r.headers.get("x-gateway-degraded") else "ok"
    try:
        return (r.json().get("error") or {}).get("code") or str(r.status_code)
    except ValueError:
        return str(r.status_code)


def line(t: float, per_app: dict, replicas: Counter) -> str:
    parts = []
    for app, (short, _) in APPS.items():
        c = per_app.get(app) or Counter()
        parts.append(f"{short} " + (", ".join(f"{k} {v}" for k, v in sorted(c.items())) or "-"))
    reps = ", ".join(f"{k} {v}" for k, v in sorted(replicas.items())) or "-"
    return f"{t:>5.0f} s | " + " | ".join(parts) + f" | replicas {reps}"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m apps.traffic")
    ap.add_argument("--seconds", type=int, default=150)
    ap.add_argument("--per-second", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=32)
    a = ap.parse_args(argv)
    from apps.client import Sender

    rng = random.Random(a.seed)
    pools = {app: units(app) for app in APPS}
    senders = {app: Sender(app, "gateway") for app in APPS}
    for s in senders.values():
        s.token()                      # each app gets its token before the hour starts, as a running app has one
    totals = {app: Counter() for app in APPS}
    window, replicas = {app: Counter() for app in APPS}, Counter()
    print(f"Traffic through the gateway for {a.seconds} s, about {a.per_second:g} requests a second (Ctrl+C stops)")
    start = time.monotonic()
    next_line, n = 10.0, 0
    try:
        while time.monotonic() - start < a.seconds:
            app = rng.choices(list(APPS), [w for _, w in APPS.values()])[0]
            u = rng.choice(pools[app])
            n += 1
            for row in u.rows:
                path, body = request_for(app, row, "gateway")
                try:
                    r = senders[app].send(path, body, extra_headers={"x-run-id": f"{u.run_id}:{n}",
                                                                     "x-sim-repeat": str(u.repeat)})
                    code = label(r)
                    rep = r.headers.get("x-gateway-replica")
                    if rep:
                        replicas[rep] += 1
                except httpx.HTTPError as e:
                    code = type(e).__name__
                window[app][code] += 1
                totals[app][code] += 1
                time.sleep(1 / a.per_second)
                now = time.monotonic() - start
                if now >= next_line:
                    print(line(next_line, window, replicas), flush=True)
                    window, replicas = {x: Counter() for x in APPS}, Counter()
                    next_line += 10
                if code not in ("ok", "degraded"):
                    break                  # the app hands this unit to a person
    except KeyboardInterrupt:
        pass
    if any(window.values()):
        print(line(time.monotonic() - start, window, replicas))
    print("Total: " + " | ".join(f"{APPS[app][0]} " + ", ".join(f"{k} {v}" for k, v in sorted(c.items()))
                                 for app, c in totals.items() if c))


if __name__ == "__main__":
    main()
