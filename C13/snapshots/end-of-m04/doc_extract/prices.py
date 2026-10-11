"""List prices of the models the course recorded, in US$ per 1 million tokens (input, output).

Source: the Azure list price of the course's deployments (global standard, pay per token), the same
prices the other courses used. Prices change: check your provider's price page before you plan.
"""

PER_MILLION = {
    "chat-strong": (2.00, 10.00),  # the vision model the course recorded
    "chat-small": (0.10, 0.50),  # a small text-only model (it cannot read pictures)
}


def cost(tokens_in: int | None, tokens_out: int | None, model: str = "chat-strong") -> float:
    p_in, p_out = PER_MILLION[model]
    return ((tokens_in or 0) * p_in + (tokens_out or 0) * p_out) / 1_000_000
