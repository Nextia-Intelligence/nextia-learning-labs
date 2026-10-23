"""get_order through an MCP server (optional: RESOLVER_TOOLS=mcp, and requirements-mcp.txt).

The workflow starts the server over stdio for each call (simple, slow: about a second) and calls its tool. The
MCP SDK puts the current trace context into the request's `_meta` (traceparent) and makes a CLIENT span
("MCP send tools/call get_order"); the server continues the same trace. Our own `execute_tool get_order` span
is the parent of both, so the run stays one story across the two processes.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from opentelemetry import trace

from . import telemetry
from .tools import ToolResult

SERVER = Path(__file__).resolve().parent / "mcp_server.py"


def _global_provider() -> None:
    """The MCP SDK uses OpenTelemetry's global tracer provider: make it ours (once per process)."""
    if not getattr(_global_provider, "done", False):
        trace.set_tracer_provider(telemetry.get().tracer_provider)
        _global_provider.done = True


async def _call(order_id: str, customer_id: str, db: Path) -> str:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    env = {**os.environ, "LARKFIELD_CUSTOMER": customer_id, "LARKFIELD_DB": str(db),
           "OBS_TELEMETRY": str(telemetry.get().folder)}
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            r = await session.call_tool("get_order", {"order_id": order_id})
            return r.content[0].text


def get_order(arguments: dict, customer_id: str, world) -> ToolResult:
    _global_provider()
    text = asyncio.run(_call(arguments.get("order_id", ""), customer_id, world.path))
    body = json.loads(text)
    if body.get("ok"):
        data = body["result"]
        return ToolResult(True, data, order_ids=[data.get("order_id")] if isinstance(data, dict) else [])
    return ToolResult(False, error=body.get("error", ""), code="not_found")
