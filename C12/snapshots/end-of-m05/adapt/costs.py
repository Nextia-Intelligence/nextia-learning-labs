"""Running costs, side by side: the hosted model now, the local adapter, a hosted fine-tune (Module 5).

Three kinds of number, each labelled: measured (saved runs), price (prices.toml, list prices that change), assumption.
"""

import json
import statistics
import tomllib
from pathlib import Path

from .cases import load_cases

ROOT = Path(__file__).resolve().parents[1]
HOURS_PER_MONTH = 730
DAY_NOTE = {822: "assumption: Larkfield's average day"}


def load_prices(path: Path = ROOT / "prices.toml") -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def hosted_per_ticket(split: str = "dev") -> tuple[float, float, float]:
    """(mean US$ per ticket, median tokens in, median tokens out) of the recorded hosted run."""
    ids = {c.case_id for c in load_cases((split,))}
    path = ROOT / "runs/predictions/chat-small.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r["case_id"] in ids]
    return (statistics.mean(r["cost_usd"] for r in rows), statistics.median(r["tokens_in"] for r in rows),
            statistics.median(r["tokens_out"] for r in rows))


def local_seconds(system: str = "adapter-long", split: str = "dev") -> float:
    ids = {c.case_id for c in load_cases((split,))}
    path = ROOT / f"runs/predictions/{system}.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    return statistics.median(r["seconds"] for r in rows if r["case_id"] in ids)


def report(tickets_per_day: int, run: str = "lora-r8-long") -> list[str]:
    prices = load_prices()
    per_ticket, tin, tout = hosted_per_ticket()
    seconds = local_seconds()
    summary = json.loads((ROOT / f"runs/{run}/summary.json").read_text(encoding="utf-8"))
    nano = prices["nano_fine_tuned"]
    train_tokens = summary["train_tokens"]
    return [
        f"{tickets_per_day} tickets a day ({DAY_NOTE.get(tickets_per_day, 'assumption')}).",
        "",
        "Hosted model now (chat-small, recorded run, dev):",
        f"  measured: US${per_ticket * 1000:.2f} per 1,000 tickets (median {tin:.0f} tokens in, {tout:.0f} out)",
        f"  = US${per_ticket * tickets_per_day:.2f} a day, US${per_ticket * tickets_per_day * 30:.2f} a month",
        "",
        "Local adapter (this computer, 2 threads, dev):",
        f"  measured: median {seconds:.2f} s per ticket = {seconds * tickets_per_day / 60:.1f} minutes of CPU a day",
        "  assumption: it runs on a computer you already have; its price, power and upkeep are not counted",
        f"  measured: training took {summary['train_seconds'] / 60:.1f} minutes once ({train_tokens:,} tokens seen)",
        "",
        "Hosted fine-tune (list prices from prices.toml; prices change: check the current page; not run here):",
        "  price: training gpt-4.1-nano on the same tokens: "
        f"US${train_tokens / 1e6 * nano['training_per_1m_tokens']:.2f}",
        f"  price: hosting the fine-tuned model: US${nano['hosting_per_hour']:.2f} an hour = "
        f"US${nano['hosting_per_hour'] * HOURS_PER_MONTH:,.0f} a month ({HOURS_PER_MONTH} hours), before any ticket",
        "  (token counts here are this course's tokenizer; the hosted model counts its own way: an assumption)",
    ]
