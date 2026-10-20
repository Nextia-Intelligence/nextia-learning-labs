"""The safety filter: messages that the assistant refuses before the model sees them."""

from .corpus import fold

# Words that start a refusal.
BLOCKED_WORDS = ["weapon", "bomb", "explosive", "suicide"]


def blocked(message: str) -> str | None:
    """The blocked word found in the message, or None."""
    text = fold(message)
    for word in BLOCKED_WORDS:
        if word in text:
            return word
    return None
