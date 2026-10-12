"""ops rollout: which release does the work, in the database the service uses.

    python -m ops rollout status
    python -m ops rollout start 1.5.0-3f9a1c                       the active release
    python -m ops rollout canary 1.5.0-8b20d4 --share 0.1           10% of the tickets
    python -m ops rollout shadow 1.5.0-8b20d4                       beside the active one, unseen
    python -m ops rollout promote                                   the canary becomes active
    python -m ops rollout rollback --reason "answers without text"  back to the last good state
    python -m ops rollout history

The worker reads the state every 5 seconds. Every change is saved in release_events, with who
made it and why: the timeline of a rollout and the evidence of a rollback. Each release must
have its manifest in operations/releases/ and match the files (python -m ops release verify).
"""

import getpass
import os

from ops.telemetry import table

ACTIONS = ("status", "start", "canary", "shadow", "promote", "rollback", "stop", "history")


def register(commands) -> None:
    p = commands.add_parser("rollout", help="active, canary and shadow releases (the database)")
    p.add_argument("action", choices=ACTIONS)
    p.add_argument("release", nargs="?", help="a release ID (start, canary, shadow)")
    p.add_argument("--share", type=float, default=0.1, help="the canary's share of tickets")
    p.add_argument("--reason", default="", help="why (saved with the change)")
    p.add_argument("--by", default=None, help="who (default: your user name)")
    p.set_defaults(run=run)


def connect():
    import psycopg
    from psycopg.rows import dict_row

    from ticket_api.config import load_env

    load_env()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is not set (see .env.example)")
    return psycopg.connect(url, row_factory=dict_row, autocommit=False)


def check_release(release_id: str) -> None:
    from ticket_api import releases

    problems = releases.check(releases.load(release_id))
    if problems:
        raise ValueError(f"release {release_id} does not match the files: " + "; ".join(problems))


def save(conn, action: str, new: dict, by: str, reason: str) -> None:
    conn.execute(
        "INSERT INTO release_state (id, active, canary, canary_share, shadow, changed_by, reason)"
        " VALUES (1, %(active)s, %(canary)s, %(canary_share)s, %(shadow)s, %(by)s, %(reason)s)"
        " ON CONFLICT (id) DO UPDATE SET active = excluded.active, canary = excluded.canary,"
        " canary_share = excluded.canary_share, shadow = excluded.shadow,"
        " changed_at = now(), changed_by = excluded.changed_by, reason = excluded.reason",
        new | {"by": by, "reason": reason},
    )
    conn.execute(
        "INSERT INTO release_events (action, active, canary, canary_share, shadow, changed_by,"
        " reason) VALUES (%(action)s, %(active)s, %(canary)s, %(canary_share)s, %(shadow)s,"
        " %(by)s, %(reason)s)",
        new | {"action": action, "by": by, "reason": reason},
    )


def describe(state: dict | None) -> str:
    if not state:
        return "no release state: the worker uses RELEASE_ID (or ASSISTANT_PROMPT)"
    text = f"active {state['active']}"
    if state["canary"]:
        text += f", canary {state['canary']} for {state['canary_share']:.0%} of tickets"
    if state["shadow"]:
        text += f", shadow {state['shadow']}"
    return text


def run(args) -> int:
    by = args.by or getpass.getuser()
    with connect() as conn:
        state = conn.execute("SELECT * FROM release_state WHERE id = 1").fetchone()
        if args.action == "status":
            print(describe(state))
            return 0
        if args.action == "history":
            rows = conn.execute("SELECT * FROM release_events ORDER BY event_id").fetchall()
            t0 = rows[0]["at"] if rows else None
            print(
                table(
                    [
                        [
                            f"+{(r['at'] - t0).total_seconds() / 60:.1f} min",
                            r["action"],
                            describe(r),
                            r["changed_by"],
                            r["reason"],
                        ]
                        for r in rows
                    ],
                    ["when", "action", "state after", "by", "reason"],
                )
            )
            return 0
        current = dict(state) if state else None
        if args.action in ("start", "canary", "shadow"):
            if not args.release:
                raise ValueError(f"rollout {args.action} needs a release ID")
            check_release(args.release)
        if args.action == "start":
            new = {"active": args.release, "canary": None, "canary_share": 0.0, "shadow": None}
        else:
            if current is None:
                raise ValueError("no active release: run python -m ops rollout start RELEASE first")
            new = {k: current[k] for k in ("active", "canary", "canary_share", "shadow")}
            if args.action == "canary":
                if not 0 < args.share <= 1:
                    raise ValueError("--share must be more than 0 and at most 1")
                new |= {"canary": args.release, "canary_share": args.share}
            elif args.action == "shadow":
                new["shadow"] = args.release
            elif args.action == "promote":
                if not current["canary"]:
                    raise ValueError("there is no canary to promote")
                new |= {"active": current["canary"], "canary": None, "canary_share": 0.0}
            elif args.action == "stop":
                new |= {"canary": None, "canary_share": 0.0, "shadow": None}
            elif args.action == "rollback":
                if current["canary"] or current["shadow"]:
                    new |= {"canary": None, "canary_share": 0.0, "shadow": None}
                else:
                    before = conn.execute(
                        "SELECT active FROM release_events WHERE active <> %s"
                        " ORDER BY event_id DESC LIMIT 1",
                        (current["active"],),
                    ).fetchone()
                    if before is None:
                        raise ValueError("nothing to roll back to")
                    new["active"] = before["active"]
        save(conn, args.action, new, by, args.reason)
    print(f"{args.action}: {describe(new)}. The worker takes it within 5 seconds.")
    return 0
