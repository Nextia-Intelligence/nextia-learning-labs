"""Send practice tickets to the live service: the evaluation course's 271 made-up tickets.

    python -m scripts.practice --tickets 100 --rate 1 [--url http://127.0.0.1:8000]

The tickets are in data/practice/tickets.jsonl: made-up tickets (no real customer wrote
them) with the labels that Grace's team gave them. For those exact messages the simulated
provider answers with REAL recorded answers of the assistant (replayed); a message that you
write yourself gets a simulated answer.

It sends one ticket every 1/rate seconds (customers do not wait for each other), as a random
customer of the small data, and saves what it sent in practice/sent.jsonl (the ticket's ID,
the practice ticket's ID and the time), so that later steps can match the tickets with their
labels.
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

from ticket_api.config import load_env

TICKETS = Path("data/practice/tickets.jsonl")
SENT = Path("practice/sent.jsonl")
CUSTOMERS = [f"C-{n:04d}" for n in range(1, 41)]  # the customers of the small data


def load_tickets(path: Path = TICKETS) -> list[dict]:
    """The practice tickets that a customer can send: not the 3 with only an attachment and no
    text (the API needs a message)."""
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [r for r in rows if not r["message"].startswith("(no text)")]


def subject_of(message: str) -> str:
    """The website makes a short subject from the first sentence."""
    first = message.strip().split("\n", 1)[0]
    for end in (". ", "? ", "! "):
        if end in first:
            first = first.split(end, 1)[0]
    return (first[:77] + "...") if len(first) > 80 else first or "Ticket from the website"


def body_of(ticket: dict, customer: str) -> dict:
    return {
        "customer_id": customer,
        "subject": subject_of(ticket["message"]),
        "body": ticket["message"],
        "channel": "web_form",
    }


def choose(tickets: list[dict], n: int, rng: random.Random, weights: dict | None = None) -> list:
    """n tickets drawn at random (with repeats). weights: {slice or language: factor}."""
    w = [
        (weights or {}).get(t["slice"], 1.0) * (weights or {}).get(f"lang:{t['language']}", 1.0)
        for t in tickets
    ]
    return rng.choices(tickets, weights=w, k=n)


async def send(url: str, chosen: list[dict], rate: float, headers: dict, rng: random.Random):
    statuses: Counter = Counter()
    SENT.parent.mkdir(exist_ok=True)
    out = SENT.open("a", encoding="utf-8")
    limits = httpx.Limits(max_connections=100)
    async with httpx.AsyncClient(base_url=url, headers=headers, timeout=60, limits=limits) as c:

        async def one(ticket: dict) -> None:
            try:
                r = await c.post("/v1/tickets", json=body_of(ticket, rng.choice(CUSTOMERS)))
            except httpx.HTTPError as error:
                statuses[type(error).__name__] += 1
                return
            statuses[r.status_code] += 1
            if r.status_code < 300:
                row = {"ticket_id": r.json()["ticket_id"], "case_id": ticket["case_id"]}
                out.write(json.dumps(row | {"sent": round(time.time(), 3)}) + "\n")

        tasks = []
        t0 = time.perf_counter()
        for i, ticket in enumerate(chosen):
            delay = t0 + i / rate - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)
            tasks.append(asyncio.create_task(one(ticket)))
        await asyncio.gather(*tasks)
    out.close()
    return statuses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickets", type=int, default=100)
    parser.add_argument("--rate", type=float, default=1.0, help="tickets per second")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--seed", type=int, default=25)
    args = parser.parse_args(argv)
    load_env()
    headers = {"X-API-Key": os.environ["API_KEY"]} if os.environ.get("API_KEY") else {}
    rng = random.Random(args.seed)
    chosen = choose(load_tickets(), args.tickets, rng)
    started = time.perf_counter()
    statuses = asyncio.run(send(args.url, chosen, args.rate, headers, rng))
    print(
        f"Sent {len(chosen)} practice tickets in {time.perf_counter() - started:.1f} s: "
        + ", ".join(f"{k}: {v}" for k, v in sorted(statuses.items(), key=str))
    )
    print(f"Saved the ticket IDs in {SENT}. The worker does their AI work; watch it with")
    print("  python -m scripts.queue_watch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
