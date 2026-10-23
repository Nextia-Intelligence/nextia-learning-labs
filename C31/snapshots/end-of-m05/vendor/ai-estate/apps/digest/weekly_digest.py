"""Weekly digest: a summary of the week's customer messages, for the Monday meeting.

    python apps/digest/weekly_digest.py

Someone wrote this script to save an hour every Monday. It runs on a build runner every week. It sends
the week's customer messages to Fernway, a model provider that Larkfield has no contract with, with a
personal key, and prints the summary. Nobody registered it.

This script is part of the course's practice estate: Fernway is a made-up provider, played by the
provider simulator on your computer, and the key below is a made-up practice key that only the simulator
accepts. The script is kept as it was found, so that the discovery lessons can find it.
"""

import json
import os
import urllib.request
from pathlib import Path

FERNWAY_URL = os.environ.get("FERNWAY_URL", "http://127.0.0.1:8320/fernway/v1")
FERNWAY_KEY = "sim-fw-personal-7Q2K9XW4"  # my own account, for now
MODEL = "fernway-swift"
TICKETS = Path(__file__).resolve().parents[2] / "data" / "tickets.jsonl"
WEEK = 40  # the number of messages in one week of the practice data


def week_messages() -> list[str]:
    rows = [json.loads(line) for line in TICKETS.read_text(encoding="utf-8").splitlines() if line]
    return [r["message"] for r in rows if r["language"] == "en" and not r["message"].startswith("(no text)")][:WEEK]


def digest_request(messages: list[str]) -> dict:
    listing = "\n".join(f"- {m}" for m in messages)
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You summarise customer support messages for a weekly team meeting."},
            {"role": "user", "content": "Summarise the main complaints of this week in five bullet points, and "
                                        "name the products that come up most.\n\nMessages:\n" + listing},
        ],
        "max_tokens": 400,
    }


def main() -> None:
    body = json.dumps(digest_request(week_messages())).encode("utf-8")
    req = urllib.request.Request(FERNWAY_URL.rstrip("/") + "/chat/completions", data=body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {FERNWAY_KEY}",
        "X-Sim-Host": "build-runner-3",  # practice only: tells the simulator which machine sent this (its egress log)
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        answer = json.loads(r.read())
    print(answer["choices"][0]["message"]["content"])
    usage = answer.get("usage", {})
    print(f"\n({usage.get('prompt_tokens')} tokens in, {usage.get('completion_tokens')} out)")


if __name__ == "__main__":
    main()
