"""How the estate's apps send their requests: straight to a provider with a key, or to the gateway with a token.

The `Sender` counts what came back (status, model that answered, cost), so every replay ends with a summary.
"""

import json
import os
import time
import uuid
from collections import Counter
from pathlib import Path

import httpx

from apps.replay import APPS

PROJECT = Path(__file__).resolve().parent.parent
PRICES = {"chat-small": (0.10, 0.50), "chat-strong": (2.00, 10.00), "embed-small": (0.02, 0.0), "gemma3:4b": (0, 0)}


class Credentials:
    """The app's own credential on the platform (state/credentials/<app>.json), and its cached tokens."""

    def __init__(self, app: str, client: httpx.Client, estate_url: str):
        state = Path(os.environ.get("ESTATE_STATE", PROJECT / "state"))
        path = Path(os.environ.get("ESTATE_CREDENTIALS_DIR", state / "credentials")) / f"{app}.json"
        if not path.exists():
            raise SystemExit(f"No credentials for {app} ({path}). Register it and run: "
                             f"python -m estate credentials issue {app}")
        c = json.loads(path.read_text())
        self.client_id, self._secret = c["client_id"], c["client_secret"]
        self.client, self.url = client, estate_url
        self._token, self._until = "", 0.0

    def __repr__(self):
        return f"Credentials({self.client_id!r})"

    def token(self) -> str:
        if self._token and self._until > time.time() + 30:
            return self._token
        r = self.client.post(self.url + "/oauth/token", json={"grant_type": "client_credentials",
                                                              "client_id": self.client_id,
                                                              "client_secret": self._secret,
                                                              "audience": "model-gateway"})
        if r.status_code != 200:
            raise SystemExit(f"The platform refused a token for {self.client_id}: {r.text[:300]}")
        d = r.json()
        self._token, self._until = d["access_token"], time.time() + d["expires_in"]
        return self._token


class Sender:
    def __init__(self, app: str, via: str = "direct", client: httpx.Client | None = None,
                 provsim_url: str | None = None, gateway_url: str | None = None, estate_url: str | None = None,
                 token=None):
        env = os.environ
        self.app, self.via = app, via
        self.cfg = APPS[app]
        self.client = client or httpx.Client(timeout=120)
        self.provsim = (provsim_url or env.get("PROVSIM_URL", "http://127.0.0.1:8320")).rstrip("/")
        self.gateway = (gateway_url or env.get("ESTATE_GATEWAY_URL", "http://127.0.0.1:8322/v1")).rstrip("/")
        self.estate = (estate_url or env.get("ESTATE_URL", "http://127.0.0.1:8321")).rstrip("/")
        self.token = token
        if via == "gateway" and token is None:
            self.token = Credentials(app, self.client, self.estate).token
        self.status = Counter()
        self.models = Counter()
        self.codes = Counter()
        self.cost = 0.0
        self.tokens_in = self.tokens_out = 0
        self.lines: list[str] = []
        self.sent = 0
        self.session = uuid.uuid4().hex[:6]     # this replay's part of each run ID (the gateway's step limit counts per run)

    def send(self, path: str, body: dict, unit=None, extra_headers: dict | None = None) -> httpx.Response:
        headers = {"x-sim-host": self.cfg["host"]}
        if unit is not None:
            headers["x-sim-repeat"] = str(unit.repeat)
        if self.via == "direct":
            url = f"{self.provsim}/{self.cfg['provider']}{path}"
            headers["api-key"] = self.cfg["key"]
        else:
            url = self.gateway + path[len("/v1"):]
            headers["authorization"] = "Bearer " + self.token()
            if unit is not None:      # a replay that sends a recorded unit again is a new run: its own run ID
                headers["x-run-id"] = f"{unit.run_id}:{self.session}"
        headers.update(extra_headers or {})
        r = self.client.post(url, json=body, headers=headers)
        self.sent += 1
        self.status[r.status_code] += 1
        try:
            data = r.json()
        except json.JSONDecodeError:
            data = {}
        if r.status_code == 200:
            model = r.headers.get("x-gateway-model") or f"{body.get('model')} ({data.get('model', '')})"
            self.models[model] += 1
            usage = data.get("usage") or {}
            self.tokens_in += int(usage.get("prompt_tokens") or 0)
            self.tokens_out += int(usage.get("completion_tokens") or 0)
            if r.headers.get("x-gateway-cost-usd"):
                self.cost += float(r.headers["x-gateway-cost-usd"])
            else:   # the model that answered: the gateway's header, or the deployment the app asked for
                deployment = (r.headers.get("x-gateway-model") or body.get("model") or "").split(" ")[0]
                p = PRICES.get(deployment, (0, 0))
                self.cost += (int(usage.get("prompt_tokens") or 0) * p[0] + int(usage.get("completion_tokens") or 0)
                              * p[1]) / 1e6
        else:
            err = data.get("error") or {}
            self.codes[err.get("code") or str(r.status_code)] += 1
        self.lines.append(f"{r.status_code} {body.get('model')} -> {r.headers.get('x-gateway-model', '')} "
                          f"{(data.get('error') or {}).get('code', '')}".rstrip())
        return r

    def summary(self, verbose: bool = False) -> str:
        out = []
        if verbose:
            out += self.lines
        where = "straight to the provider" if self.via == "direct" else "through the gateway"
        out.append(f"{self.app}: {self.sent} requests {where} | status {dict(sorted(self.status.items()))}")
        if self.models:
            out.append("answered by: " + ", ".join(f"{m} x{n}" for m, n in self.models.most_common()))
        if self.codes:
            out.append("refused or failed: " + ", ".join(f"{c} x{n}" for c, n in self.codes.most_common()))
        out.append(f"tokens: {self.tokens_in:,} in, {self.tokens_out:,} out | cost: US${self.cost:.4f}")
        return "\n".join(out)
