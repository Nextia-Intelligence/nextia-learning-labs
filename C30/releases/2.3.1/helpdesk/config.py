"""Settings. Every setting can come from an environment variable."""

import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
DATA = PACKAGE / "data"
POLICIES = DATA / "policies"
PROMPTS = PACKAGE / "prompts"


def home() -> Path:
    """The folder for the app's working files: the store and the traces."""
    p = Path(os.environ.get("HELPDESK_HOME") or PACKAGE.parent / ".helpdesk")
    p.mkdir(parents=True, exist_ok=True)
    return p


# The app's date is fixed, so that order dates and policy versions give the same
# answers on every computer and every day.
TODAY = os.environ.get("HELPDESK_TODAY", "2026-11-16")

# How many policy sections the assistant reads for one question.
RETRIEVAL_K = int(os.environ.get("HELPDESK_RETRIEVAL_K", "3"))

# The longest message that the assistant reads, in characters.
MAX_INPUT_CHARS = 1200

DEFAULT_CUSTOMER = os.environ.get("HELPDESK_CUSTOMER", "C-1001")
DEFAULT_PORT = int(os.environ.get("HELPDESK_PORT", "8730"))

# Optional live mode: an OpenAI-compatible endpoint (your own key or a local model).
LIVE_URL = os.environ.get("HELPDESK_LIVE_URL", "")
LIVE_MODEL = os.environ.get("HELPDESK_LIVE_MODEL", "")
LIVE_TEMPERATURE = os.environ.get("HELPDESK_LIVE_TEMPERATURE", "")
# Extra request fields as JSON, for providers that need them, for example {"reasoning_effort": "none"}.
LIVE_EXTRA = os.environ.get("HELPDESK_LIVE_EXTRA", "")


def live_key() -> str:
    """The key for live mode. It is never printed, logged or exported."""
    return os.environ.get("HELPDESK_LIVE_KEY", "")
