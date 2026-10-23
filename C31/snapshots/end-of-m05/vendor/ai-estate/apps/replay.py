"""Replay an app's real recorded requests: exactly the bodies that the earlier course sent, in order.

    python -m apps.replay ticket-triage --units 5                 straight to the provider (before the gateway)
    python -m apps.replay ticket-triage --units 5 --via gateway   through the gateway, with the app's own token

The apps of Larkfield's estate and their recorded streams (apps/streams/, made from the earlier courses):

    ticket-triage       the MLOps course's triage step: one chat call (prompt v2) and one embedding per ticket
    support-workflow    the agents course's structured agent on chat-strong: 1 to 5 calls per task
    doc-assistant       the capstone course's document assistant: one call per question
    release-judge       the evaluation course's reference judge on chat-strong: one call per reply

Before the gateway, each app calls the provider with its own key (a shared team key or a personal key) and
the model's deployment name. Through the gateway, it sends the same body with its own access token and a
capability name instead (--model-names deployment keeps the old names: the gateway accepts them as aliases,
with a warning). A "unit" is one ticket, one task run, one question or one reply.
"""

import argparse
import gzip
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

STREAMS = Path(__file__).resolve().parent / "streams"

APPS = {
    "ticket-triage": {"stream": "ticket-triage", "provider": "azure", "key": "sim-az-service-team-0001",
                      "host": "triage-svc-01", "capabilities": {"chat-small": "fast-small", "embed-small": "embed"},
                      "per_unit": "ticket"},
    "support-workflow": {"stream": "support-workflow__chat-strong", "provider": "azure",
                         "key": "sim-az-service-team-0001", "host": "workflow-01",
                         "capabilities": {"chat-strong": "strong-reasoning", "chat-small": "fast-small"},
                         "per_unit": "task run"},
    "doc-assistant": {"stream": "doc-assistant__chat", "provider": "azure", "key": "sim-az-data-team-0002",
                      "host": "docs-01", "capabilities": {"chat-small": "fast-small"}, "per_unit": "question"},
    "release-judge": {"stream": "release-judge__chat-strong", "provider": "azure", "key": "sim-az-priya-0003",
                      "host": "priya-laptop", "capabilities": {"chat-strong": "strong-reasoning"},
                      "per_unit": "reply judged"},
}


@dataclass
class Unit:
    app: str
    group: str
    repeat: int
    rows: list[dict] = field(default_factory=list)

    @property
    def run_id(self) -> str:
        return f"{self.app}:{self.group}:r{self.repeat}"


def load_stream(name: str) -> list[dict]:
    with gzip.open(STREAMS / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def units(app: str, stream: str | None = None) -> list[Unit]:
    """The app's units in recorded order. Triage: every recorded repeat of a ticket is its own unit."""
    rows = load_stream(stream or APPS[app]["stream"])
    by: dict[tuple, Unit] = {}
    for r in rows:
        if app == "ticket-triage" and r["step"] == 2:     # the embedding goes with every repeat of its ticket
            for (g, rep), u in by.items():
                if g == r["group"]:
                    u.rows.append(r)
            continue
        key = (r["group"], r["repeat"])
        by.setdefault(key, Unit(app, r["group"], r["repeat"])).rows.append(r)
    for u in by.values():
        u.rows.sort(key=lambda r: (r["step"], r["seq"]))
    return list(by.values())


def request_for(app: str, row: dict, via: str, model_names: str = "capability") -> tuple[str, dict]:
    body = dict(row["body"])
    if via == "gateway":
        body.pop("reasoning_effort", None)     # the platform adds the settings a model needs (the mapping)
        if model_names == "capability":
            body["model"] = APPS[app]["capabilities"][body["model"]]
    return row["endpoint"], body


def pick(app: str, n: int, seed: int = 32, order: str = "random") -> list[Unit]:
    all_units = units(app)
    if order == "recorded" or n >= len(all_units):
        return all_units[:n]
    return random.Random(seed).sample(all_units, n)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m apps.replay")
    ap.add_argument("app", choices=list(APPS))
    ap.add_argument("--units", type=int, default=5)
    ap.add_argument("--via", choices=["direct", "gateway"], default="direct")
    ap.add_argument("--model-names", choices=["capability", "deployment"], default="capability")
    ap.add_argument("--seed", type=int, default=32)
    ap.add_argument("--order", choices=["random", "recorded"], default="random")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    from apps.client import Sender

    sender = Sender(a.app, a.via)
    for u in pick(a.app, a.units, a.seed, a.order):
        for row in u.rows:
            path, body = request_for(a.app, row, a.via, a.model_names)
            sender.send(path, body, u)
    print(sender.summary(verbose=a.verbose))


if __name__ == "__main__":
    main()
