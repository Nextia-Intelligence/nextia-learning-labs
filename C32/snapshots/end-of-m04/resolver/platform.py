"""The workflow on Larkfield's platform (added by the governance course; the rest of resolver/ is the agents course's).

One setting moves the workflow's model calls behind the platform's controls:

    RESOLVER_PROVIDER=gateway   every model call goes to the model gateway (ESTATE_GATEWAY_URL), with the
                                workflow's own access token; RESOLVER_MODEL names a capability (strong-reasoning)

The workflow's credential is its registration's client ID and secret (python -m estate credentials issue
support-workflow writes them to state/credentials/support-workflow.json; ESTATE_CREDENTIALS names the file).
"""

import json
import os
import secrets
import time
import urllib.error
import urllib.request
from pathlib import Path

from .providers import Completion, OpenAICompatibleProvider, ProviderError

PROJECT = Path(__file__).resolve().parent.parent


class Estate:
    """The workflow's identity on the platform: its credentials and its tokens (one per gateway)."""

    def __init__(self):
        state = Path(os.environ.get("ESTATE_STATE", PROJECT / "state"))
        path = Path(os.environ.get("ESTATE_CREDENTIALS", state / "credentials" / "support-workflow.json"))
        if not path.exists():
            raise ProviderError(f"No credentials at {path}: run python -m estate credentials issue support-workflow")
        creds = json.loads(path.read_text())
        self.client_id, self._secret = creds["client_id"], creds["client_secret"]
        self.url = os.environ.get("ESTATE_URL", "http://127.0.0.1:8321")
        self.tokens: dict[str, tuple[str, float]] = {}

    def __repr__(self) -> str:   # never print the secret
        return f"Estate(client_id={self.client_id!r})"

    def token(self, audience: str) -> str:
        tok, until = self.tokens.get(audience, ("", 0.0))
        if tok and until > time.time() + 30:
            return tok
        body = json.dumps({"grant_type": "client_credentials", "client_id": self.client_id,
                           "client_secret": self._secret, "audience": audience}).encode()
        req = urllib.request.Request(self.url + "/oauth/token", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise ProviderError(f"The platform refused a token: {e.read().decode()[:300]}", e.code) from None
        except OSError as e:
            raise ProviderError(f"Cannot reach the platform's token endpoint: {e}") from None
        self.tokens[audience] = (data["access_token"], time.time() + data["expires_in"])
        return data["access_token"]


_ESTATE: Estate | None = None


def estate() -> Estate:
    global _ESTATE
    if _ESTATE is None:
        _ESTATE = Estate()
    return _ESTATE


def traceparent(run_id: str) -> str:
    """A W3C traceparent: one trace per run (from the run ID), a new span per call."""
    import hashlib

    trace = hashlib.sha256(run_id.encode()).hexdigest()[:32]
    return f"00-{trace}-{secrets.token_hex(8)}-01"


class GatewayProvider(OpenAICompatibleProvider):
    """The agents course's OpenAI-compatible adapter, pointed at the model gateway with the workflow's token."""

    def __init__(self, timeout_s: float = 60.0):
        super().__init__(os.environ.get("ESTATE_GATEWAY_URL", "http://127.0.0.1:8322/v1"), "pending", timeout_s)
        self.last_headers: dict = {}

    def complete(self, request: dict, meta: dict | None = None) -> Completion:
        meta = meta or {}
        self.client.api_key = estate().token("model-gateway")
        run_id = meta.get("run_id") or f"{meta.get('task_id')}-{meta.get('variant')}"
        headers = {"X-Run-Id": run_id, "traceparent": traceparent(run_id)}
        if meta.get("repeat"):
            headers["X-Sim-Repeat"] = str(meta["repeat"])   # practice: which recorded repeat to replay
        start = time.monotonic()
        from .providers import translate_errors

        with translate_errors():
            raw = self.client.chat.completions.with_raw_response.create(**request, extra_headers=headers)
        self.last_headers = dict(raw.headers)
        response = raw.parse()
        return Completion.from_response(response.model_dump(), round(time.monotonic() - start, 3))
