"""The order lookup as an MCP server (the agents course's optional example, with telemetry). Started by mcp_tools.py.

The MCP SDK (2.3.0) makes a SERVER span for every request ("tools/call get_order") and takes its parent from the
request's `_meta.traceparent`, which the SDK's client put there. So the server's work joins the workflow's trace,
in another process. This process records its spans into the same telemetry folder (OBS_TELEMETRY).
The customer is not a tool argument: the host that starts the server sets it (LARKFIELD_CUSTOMER).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from opentelemetry import trace  # noqa: E402

from resolver import telemetry  # noqa: E402
from resolver.systems import World  # noqa: E402
from resolver.tools import _run_read  # noqa: E402

T = telemetry.Telemetry(export=os.environ.get("OBS_EXPORT", "file"))
T.tracer_provider.add_span_processor  # the SDK uses the global provider: make ours the global one
trace.set_tracer_provider(T.tracer_provider)

from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

CUSTOMER = os.environ.get("LARKFIELD_CUSTOMER", "")
DB = Path(os.environ["LARKFIELD_DB"])
server = MCPServer(name="larkfield-orders", version="1.0.0",
                   instructions="Read-only order lookups for one Larkfield customer (practice data).")


@server.tool(name="get_order", annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
def get_order(order_id: str) -> str:
    """Look up one of this customer's orders by its order ID (LK- and 6 digits). Read-only."""
    result = _run_read("get_order", {"order_id": order_id}, CUSTOMER, World(DB, "mcp"))
    span = trace.get_current_span()
    span.set_attribute("larkfield.tool.status", result.code)
    span.set_attribute("larkfield.mcp.server", "larkfield-orders")
    T.flush()
    return result.for_model()


if __name__ == "__main__":
    try:
        server.run()
    finally:
        T.shutdown()
