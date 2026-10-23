"""Model calls through the agents governance course's model gateway (RESOLVER_PROVIDER=gateway).

Copied from that course's resolver/platform.py (commit 16d18f03, the vendored estate in vendor/ai-estate) with
ONE change that this course is about: that course sent a traceparent MADE FROM THE RUN ID (one made-up trace per
run, a random span per call), so the gateway's usage records could not be joined to the workflow's own traces.
Here every call sends the traceparent of the workflow's real `chat` span, and the X-Run-Id. The gateway's answer
headers (the model that really answered, the request ID, the cost it charged) go on the same span.

    RESOLVER_PROVIDER=gateway RESOLVER_MODEL=strong-reasoning python -m resolver run T-90103 --variant agent_structured
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from opentelemetry import trace

from . import conventions as c
from . import telemetry
from .providers import Completion, OpenAICompatibleProvider, ProviderError

PROJECT = Path(__file__).resolve().parent.parent
ESTATE = PROJECT / "vendor" / "ai-estate"


class Estate:
    """The workflow's identity on the platform: its credentials and its tokens."""

    def __init__(self):
        state = Path(os.environ.get("ESTATE_STATE", ESTATE / "state"))
        path = Path(os.environ.get("ESTATE_CREDENTIALS", state / "credentials" / "support-workflow.json"))
        if not path.exists():
            raise ProviderError(f"No credentials at {path}: in vendor/ai-estate run "
                                "python -m estate credentials issue support-workflow")
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


class GatewayProvider(OpenAICompatibleProvider):
    """The OpenAI-compatible adapter, pointed at the model gateway, with the workflow's token and trace context."""

    def __init__(self, timeout_s: float = 60.0):
        super().__init__(os.environ.get("ESTATE_GATEWAY_URL", "http://127.0.0.1:8322/v1"), "pending", timeout_s)
        self.estate = Estate()
        self.last_headers: dict = {}

    def complete(self, request: dict, meta: dict | None = None) -> Completion:
        from . import observe
        meta = meta or {}
        self.client.api_key = self.estate.token("model-gateway")
        run = observe.current()
        headers = {"X-Run-Id": run.run_id if run else f"{meta.get('task_id')}-{meta.get('variant')}"}
        tp = telemetry.current_traceparent()
        if tp and os.environ.get("OBS_GATEWAY_CONTEXT", "on") == "on":
            headers["traceparent"] = tp                        # the real chat span: the gateway can join it
        if meta.get("repeat"):
            headers["X-Sim-Repeat"] = str(meta["repeat"])      # practice: which recorded repeat to replay
        start = time.monotonic()
        from .providers import translate_errors
        with translate_errors():
            raw = self.client.chat.completions.with_raw_response.create(**request, extra_headers=headers)
        self.last_headers = {k.lower(): v for k, v in raw.headers.items()}
        span = trace.get_current_span()
        h = self.last_headers
        span.set_attributes(telemetry.clean({
            c.GATEWAY_MODEL: h.get("x-gateway-model"), c.GATEWAY_REQUEST_ID: h.get("x-gateway-request-id"),
            "larkfield.gateway.capability": h.get("x-gateway-capability"),
            "larkfield.gateway.provider": h.get("x-gateway-provider"),
            "larkfield.gateway.cost_usd": float(h["x-gateway-cost-usd"]) if h.get("x-gateway-cost-usd") else None,
            "larkfield.gateway.replica": h.get("x-gateway-replica")}))
        response = raw.parse()
        completion = Completion.from_response(response.model_dump(), round(time.monotonic() - start, 3))
        # The simulator answers with the recorded answer at once; its header says how long the real call took.
        if h.get("x-sim-recorded-latency-ms"):
            completion.latency_s = float(h["x-sim-recorded-latency-ms"]) / 1000
        completion.recorded_at = "gateway"
        return completion
