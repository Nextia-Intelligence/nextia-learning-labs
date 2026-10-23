"""The tool gateway by hand: commands of python -m estate.

    python -m estate tools helpdesk-assistant          the tools this agent may call, read or write
    python -m estate tool-call helpdesk-assistant support.get_ticket '{"ticket_id": "T-30002"}'
    python -m estate tool-call support-workflow orders.get_payments '{"order_id": "LK-645223"}' \\
        --customer C-55223 --ticket T-90603

`tool-call` takes a token with the agent's own credentials (state/credentials/<agent>.json), sends one call to
the tool gateway (ESTATE_TOOLS_URL) as the agent's app would, and prints the HTTP status and the answer. The
customer and the ticket go in the call's context, never in the tool's arguments.
"""

import json
import os
import sys

from estate import paths


def _token(agent: str, audience: str) -> str:
    from estate import identity

    try:
        creds = json.loads((paths.state() / "credentials" / f"{agent}.json").read_text())
    except FileNotFoundError:
        sys.exit(f"{agent} has no credentials: python -m estate credentials issue {agent}")
    try:
        return identity.token(creds["client_id"], creds["client_secret"], audience)["access_token"]
    except identity.TokenError as e:
        sys.exit(f"No token for {agent}: {e.code}: {e}")


def _send(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, dict]:
    import httpx

    url = os.environ.get("ESTATE_TOOLS_URL", f"http://127.0.0.1:{os.environ.get('TOOLGATE_PORT', '8326')}")
    try:
        r = httpx.request(method, url.rstrip("/") + path, json=body, timeout=30,
                          headers={"authorization": f"Bearer {token}"})
    except httpx.TransportError as e:
        sys.exit(f"The tool gateway at {url} cannot be reached ({type(e).__name__}). Is it running? "
                 "python -m estate status")
    return r.status_code, r.json()


def cmd_tools(a):
    status, body = _send("GET", "/v1/tools", _token(a.agent, "tool-gateway"))
    if status != 200:
        sys.exit(f"HTTP {status} {json.dumps(body)}")
    for t in body["tools"]:
        print(f"{t['tool']:<32} {t['kind']}")


def cmd_tool_call(a):
    try:
        arguments = json.loads(a.arguments or "{}")
    except json.JSONDecodeError as e:
        sys.exit(f"The arguments are not valid JSON: {e}")
    context = {k: v for k, v in (("customer_id", a.customer), ("ticket_id", a.ticket)) if v}
    status, body = _send("POST", "/v1/tools/call", _token(a.agent, a.audience),
                         {"tool": a.tool, "arguments": arguments, "context": context, "run_id": a.run_id})
    print(f"HTTP {status}")
    print(json.dumps(body, ensure_ascii=False))


ORDER = 29


def register(sub) -> dict:
    p = sub.add_parser("tools", help="the tools an agent may call through the tool gateway")
    p.add_argument("agent")
    p = sub.add_parser("tool-call", help="send one tool call to the tool gateway, with an agent's credentials")
    p.add_argument("agent")
    p.add_argument("tool", help="server.tool, for example orders.get_order")
    p.add_argument("arguments", nargs="?", help='the tool\'s arguments as JSON, for example \'{"order_id": "LK-640436"}\'')
    p.add_argument("--customer", help="the customer of the ticket (the call's context)")
    p.add_argument("--ticket", help="the ticket that the agent works on (the call's context)")
    p.add_argument("--run-id", default="by-hand", help="the run that the call belongs to")
    p.add_argument("--audience", default="tool-gateway", help="practice: the token's audience")
    return {"tools": cmd_tools, "tool-call": cmd_tool_call}
