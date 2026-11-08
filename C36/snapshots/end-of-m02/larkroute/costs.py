"""The cost table (config/costs.json): what each kind of routing mistake costs Larkfield.

A prediction is a route (one of the six teams or "needs_person") or "review" (a person reads the message
first and sends it on). The cost of one message:

- the right route: 0;
- "review": the review cost (a person then sends it to the right team);
- "needs_person" for a team's message: a senior person reads it and forwards it;
- an account takeover that does not go to the account team: the missed takeover;
- a "needs_person" message that goes to a team: the cost of a team answer to it;
- any other wrong team: the wrong queue, or the urgent wrong queue for an urgent message.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path | None = None) -> dict:
    return json.loads((path or ROOT / "config" / "costs.json").read_text())


def message_cost(true_route: str, predicted: str, priority: str, topic: str, costs: dict) -> float:
    if predicted == true_route:
        return 0.0
    if predicted == "review":
        return costs["review"]
    if predicted == "needs_person":
        return costs["team_message_sent_to_person"]
    if topic == "account_takeover":
        return costs["missed_account_takeover"]
    if true_route == "needs_person":
        return costs["needs_person_sent_to_team"]
    return costs["wrong_queue_urgent"] if priority == "urgent" else costs["wrong_queue"]


def total(truth, predicted, costs: dict) -> float:
    """The cost of all predictions, in dollars (truth: a table with route, priority and topic)."""
    return float(sum(message_cost(t, p, pr, tp, costs) for t, p, pr, tp in
                     zip(truth["route"], predicted, truth["priority"], truth["topic"], strict=True)))
