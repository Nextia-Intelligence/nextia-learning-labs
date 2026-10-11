"""Send agents' reviews of practice tickets, some time later (the MLOps course, Module 4).

    python -m scripts.send_reviews --delay 120 --share 0.5            once: the tickets old enough
    python -m scripts.send_reviews --delay 120 --share 0.5 --follow   keep going until Ctrl+C

The practice tickets carry the labels that Grace's team gave them (data/practice/tickets.jsonl):
the team that was right and whether a person had to handle the ticket. This script plays the
help desk's agents: for the tickets in practice/sent.jsonl that arrived at least --delay seconds
ago, it sends that label as a review (POST /v1/tickets/{id}/review), for a random --share of
them (agents do not review every ticket). In real life the delay is hours or days; here it is
seconds, so that a practice run shows it.
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import httpx

from scripts.practice import SENT, TICKETS
from ticket_api.config import load_env

DONE = Path("practice/reviewed.jsonl")


def labels() -> dict[str, dict]:
    rows = [json.loads(x) for x in TICKETS.read_text(encoding="utf-8").splitlines() if x]
    return {r["case_id"]: r for r in rows}


def due(now: float, delay: float, done: set[str]) -> list[dict]:
    if not SENT.exists():
        return []
    rows = [json.loads(x) for x in SENT.read_text(encoding="utf-8").splitlines() if x]
    return [r for r in rows if r["ticket_id"] not in done and r["sent"] + delay <= now]


def send(client: httpx.Client, rows: list[dict], share: float, rng: random.Random) -> tuple:
    if not rows:  # nothing is old enough yet (or no practice ticket was sent)
        return 0, 0
    truth = labels()
    sent = skipped = 0
    with DONE.open("a", encoding="utf-8") as out:
        for r in rows:
            label = truth[r["case_id"]]
            reviewed = rng.random() < share and label["expected_team"] in (
                "delivery",
                "returns",
                "payment",
                "warranty",
                "account",
            )
            if reviewed:
                agent = f"agent-{rng.randrange(1, 13):02d}"
                resp = client.post(
                    f"/v1/tickets/{r['ticket_id']}/review",
                    json={
                        "team": label["expected_team"],
                        "needs_human": label["expected_needs_human"],
                        "reviewed_by": agent,
                    },
                )
                sent += resp.status_code == 200
            else:
                skipped += 1
            out.write(json.dumps({"ticket_id": r["ticket_id"], "reviewed": reviewed}) + "\n")
    return sent, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--delay", type=float, default=120, help="seconds after the ticket")
    parser.add_argument("--share", type=float, default=0.5, help="the share of tickets reviewed")
    parser.add_argument("--follow", action="store_true", help="keep going until Ctrl+C")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--seed", type=int, default=4)
    args = parser.parse_args(argv)
    load_env()
    headers = {"X-API-Key": os.environ["API_KEY"]} if os.environ.get("API_KEY") else {}
    rng = random.Random(args.seed)
    done = set()
    if DONE.exists():
        done = {json.loads(x)["ticket_id"] for x in DONE.read_text().splitlines() if x}
    total = 0
    with httpx.Client(base_url=args.url, headers=headers, timeout=30) as client:
        try:
            while True:
                rows = due(time.time(), args.delay, done)
                sent, skipped = send(client, rows, args.share, rng)
                done |= {r["ticket_id"] for r in rows}
                total += sent
                if not args.follow:
                    print(f"Reviews sent: {sent}; tickets not reviewed: {skipped}.")
                    return 0
                time.sleep(5)
        except KeyboardInterrupt:
            print(f"Reviews sent: {total}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
