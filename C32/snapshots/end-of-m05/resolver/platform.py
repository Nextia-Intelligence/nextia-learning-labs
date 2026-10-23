"""The workflow on Larkfield's platform (added by the governance course; the rest of resolver/ is the agents course's).

Two settings move the workflow behind the platform's controls:

    RESOLVER_PROVIDER=gateway   every model call goes to the model gateway (ESTATE_GATEWAY_URL), with the
                                workflow's own access token; RESOLVER_MODEL names a capability (strong-reasoning)
    RESOLVER_TOOLS=gateway      every tool call (reads and the approved writes) goes to the tool gateway
                                (ESTATE_TOOLS_URL), which calls the orders MCP server

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
from .systems import Faults, InvalidRequest, PermissionDenied, ServiceError, ServiceTimeout, ServiceUnavailable
from .tools import ToolResult

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


class ToolGatewayWorld:
    """The practice systems behind the tool gateway: the same interface as resolver.systems.World."""

    remote = True

    def __init__(self, task, faults_seen: list | None = None, extra_faults: list | None = None, run_id: str = ""):
        self.task = task
        self.ticket_id = task.task_id
        self.customer_id = task.customer_id
        self.run_id = run_id or task.task_id
        self.faults = Faults()                 # the practice failures met so far (the orders server applies them)
        self.faults.seen = [tuple(f) for f in faults_seen or []]
        self.extra = list(extra_faults or [])  # --fault options: failures that the task does not have
        self.grant = ""
        self.url = os.environ.get("ESTATE_TOOLS_URL", "http://127.0.0.1:8326")

    def _post(self, tool: str, arguments: dict, approval: str = "") -> tuple[int, dict]:
        body = {"tool": tool, "arguments": arguments, "run_id": self.run_id, "approval": approval,
                "context": {"customer_id": self.customer_id, "ticket_id": self.ticket_id,
                            "faults_seen": [list(f) for f in self.faults.seen], "extra_faults": self.extra}}
        req = urllib.request.Request(self.url + "/v1/tools/call", data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": "Bearer " + estate().token("tool-gateway")})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.loads(r.read())
                status = r.status
        except urllib.error.HTTPError as e:
            out, status = json.loads(e.read() or b"{}"), e.code
        except OSError as e:
            raise ServiceUnavailable(f"{tool}: the tool gateway cannot be reached ({e})") from None
        if status == 200:
            self.faults.seen += [tuple(f) for f in (out.get("result") or {}).get("faults") or []]
        return status, out

    # --- reads -------------------------------------------------------------------------------------------
    def run_read(self, name: str, arguments, customer_id: str) -> ToolResult:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except json.JSONDecodeError:
                return ToolResult(False, error="The arguments are not valid JSON.", code="invalid_arguments")
        try:
            status, out = self._post(f"orders.{name}", arguments if isinstance(arguments, dict) else {})
        except ServiceError as e:   # a failure is a result, never an exception in the loop (the agents course's rule)
            return ToolResult(False, error=f"The service failed: {e}. You may try again once.", code=f"service_{e.code}")
        if status != 200:
            err = out.get("error") or {}
            return ToolResult(False, error=f"Refused by the tool gateway: {err.get('message', status)}",
                              code=f"gateway_{err.get('code', status)}")
        r = out["result"]
        if "ok" not in r:   # the server refused the call itself (for example a wrong context)
            return ToolResult(False, error=str(r.get("text", r))[:300], code="server_error")
        return ToolResult(r["ok"], r.get("data"), r.get("error", ""), r.get("code", "ok"), r.get("order_ids") or [])

    def owner(self, order_id: str):   # not used remotely: the orders server checks the owner
        return None

    def operation(self, op_id: str) -> dict | None:
        status, out = self._post("orders.get_operation", {"operation_id": op_id})
        if status != 200:
            raise ServiceUnavailable(f"get_operation: {(out.get('error') or {}).get('message', status)}")
        return out["result"].get("result")

    # --- writes ------------------------------------------------------------------------------------------
    def request_grant(self, state, approver: str) -> str:
        """Ask the platform for an approval grant for every proposed write, for the named person."""
        actions = [{"tool": f"orders.{a.tool}", "arguments": _write_args(a)} for a in state.proposal.actions]
        body = json.dumps({"run_id": self.run_id, "approver": approver, "actions": actions}).encode()
        req = urllib.request.Request(estate().url + "/v1/approvals", data=body, method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": "Bearer " + estate().token("tool-gateway")})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise PermissionError(json.loads(e.read() or b"{}").get("error", {}).get("message", e.code)) from None
        self.grant = out["grant"]
        return f"Approval grant from the platform for {approver} (rules: {', '.join(out['rules'])})."

    def _write(self, tool: str, arguments: dict) -> dict:
        status, out = self._post(f"orders.{tool}", arguments, self.grant)
        if status != 200:
            err = out.get("error") or {}
            raise PermissionDenied(f"{tool}: refused by the tool gateway: {err.get('message', status)}")
        r = out["result"]
        if r.get("ok"):
            return r["result"]
        kind = r.get("error_kind")
        cls = {"timeout": ServiceTimeout, "unavailable": ServiceUnavailable, "denied": PermissionDenied,
               "invalid": InvalidRequest}.get(kind, ServiceError)
        raise cls(r.get("error", tool))

    def create_return_label(self, op_id, order_id, sku, reason):
        return self._write("create_return_label", {"operation_id": op_id, "order_id": order_id, "sku": sku,
                                                   "reason": reason})

    def reship_item(self, op_id, order_id, sku, quantity):
        return self._write("reship_item", {"operation_id": op_id, "order_id": order_id, "sku": sku,
                                           "quantity": quantity})

    def request_refund(self, op_id, order_id, amount, reason_code, payment_id=None):
        args = {"operation_id": op_id, "order_id": order_id, "amount": amount, "reason_code": reason_code}
        if payment_id:
            args["payment_id"] = payment_id
        return self._write("request_refund", args)

    def add_ticket_note(self, op_id, text):
        return self._write("add_ticket_note", {"operation_id": op_id, "note": text})

    def changes(self):
        from .systems import World

        return World().changes()


def _write_args(action) -> dict:
    """The arguments of a proposed write, as the tool gateway will see them (without the operation ID)."""
    d = action.model_dump(exclude={"tool"})
    if action.tool == "request_refund":
        out = {"order_id": d["order_id"], "amount": d["amount"], "reason_code": d["reason_code"]}
        if d.get("payment_id"):
            out["payment_id"] = d["payment_id"]
        return out
    if action.tool == "create_return_label":
        return {"order_id": d["order_id"], "sku": d["sku"], "reason": d["reason"]}
    return {"order_id": d["order_id"], "sku": d["sku"], "quantity": d["quantity"]}
