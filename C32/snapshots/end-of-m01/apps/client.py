"""How the estate's apps send their requests: straight to a provider, with a key.

The `Sender` counts what came back (status, model that answered, cost), so every replay ends with a summary.
"""

import json
import os
from collections import Counter
from pathlib import Path

import httpx

from apps.replay import APPS

PROJECT = Path(__file__).resolve().parent.parent
PRICES = {"chat-small": (0.10, 0.50), "chat-strong": (2.00, 10.00), "embed-small": (0.02, 0.0), "gemma3:4b": (0, 0)}


class Sender:
    def __init__(self, app: str, via: str = "direct", client: httpx.Client | None = None,
                 provsim_url: str | None = None):
        self.app, self.via = app, via
        self.cfg = APPS[app]
        self.client = client or httpx.Client(timeout=120)
        self.provsim = (provsim_url or os.environ.get("PROVSIM_URL", "http://127.0.0.1:8320")).rstrip("/")
        self.status = Counter()
        self.models = Counter()
        self.codes = Counter()
        self.cost = 0.0
        self.tokens_in = self.tokens_out = 0
        self.lines: list[str] = []
        self.sent = 0

    def send(self, path: str, body: dict, unit=None, extra_headers: dict | None = None) -> httpx.Response:
        headers = {"x-sim-host": self.cfg["host"]}
        if unit is not None:
            headers["x-sim-repeat"] = str(unit.repeat)
        url = f"{self.provsim}/{self.cfg['provider']}{path}"
        headers["api-key"] = self.cfg["key"]
        headers.update(extra_headers or {})
        r = self.client.post(url, json=body, headers=headers)
        self.sent += 1
        self.status[r.status_code] += 1
        try:
            data = r.json()
        except json.JSONDecodeError:
            data = {}
        if r.status_code == 200:
            model = f"{body.get('model')} ({data.get('model', '')})"
            self.models[model] += 1
            usage = data.get("usage") or {}
            self.tokens_in += int(usage.get("prompt_tokens") or 0)
            self.tokens_out += int(usage.get("completion_tokens") or 0)
            p = PRICES.get(body.get("model"), (0, 0))
            self.cost += (int(usage.get("prompt_tokens") or 0) * p[0] + int(usage.get("completion_tokens") or 0)
                          * p[1]) / 1e6
        else:
            err = data.get("error") or {}
            self.codes[err.get("code") or str(r.status_code)] += 1
        self.lines.append(f"{r.status_code} {body.get('model')} -> {data.get('model', '')} "
                          f"{(data.get('error') or {}).get('code', '')}".rstrip())
        return r

    def summary(self, verbose: bool = False) -> str:
        out = []
        if verbose:
            out += self.lines
        where = "straight to the provider"
        out.append(f"{self.app}: {self.sent} requests {where} | status {dict(sorted(self.status.items()))}")
        if self.models:
            out.append("answered by: " + ", ".join(f"{m} x{n}" for m, n in self.models.most_common()))
        if self.codes:
            out.append("refused or failed: " + ", ".join(f"{c} x{n}" for c, n in self.codes.most_common()))
        out.append(f"tokens: {self.tokens_in:,} in, {self.tokens_out:,} out | cost: US${self.cost:.4f}")
        return "\n".join(out)
