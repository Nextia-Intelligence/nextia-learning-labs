"""orders-mcp: the agents course's practice systems behind an MCP server, for the tool gateway.

The tools are the resolution workflow's own (resolver/tools.py and resolver/systems.py, unchanged): the same
checks, the same results, byte for byte, so the workflow's recorded model decisions still replay when its
tools run here. Reads: get_order, get_customer_orders, get_payments, search_policy, get_operation. Writes:
create_return_label, reship_item, request_refund, add_ticket_note (each with an operation ID).

The customer and the ticket never come from a tool argument, so a model cannot choose them: they come in the
request's metadata (`_meta`, key larkfield/context), which the tool gateway fills from the app's context. The
practice failures of the agents course's tasks (timeouts, a service that is down, a refusal, a timeout after
a write) still happen here, per ticket: the context says which ones were already used.

Run by the tool gateway on stdio: python -m orders_mcp. Logs go to stderr.
"""

import json
import sys

from mcp.server.mcpserver import Context, MCPServer

from orders_mcp import CONTEXT_KEY, SERVER_NAME, __version__
from resolver.data import load_tasks
from resolver.systems import PRACTICE_DB, Faults, ServiceError, World
from resolver.tools import run_read

TASKS = load_tasks()


def context(ctx: Context) -> dict:
    meta = ctx.request_context.meta or {}
    c = meta.get(CONTEXT_KEY) if isinstance(meta, dict) else None
    if not isinstance(c, dict) or not c.get("customer_id") or not c.get("ticket_id"):
        raise ValueError("missing context: the tool gateway sends the customer and the ticket")
    task = TASKS.get(c["ticket_id"])
    if task and task.customer_id != c["customer_id"]:   # the ticket system says whose ticket it is
        raise ValueError(f"ticket {c['ticket_id']} is not a ticket of customer {c['customer_id']}")
    return c


def world_for(c: dict) -> World:
    """A world for this call: the ticket's practice failures, minus the ones the run has already met."""
    task = TASKS.get(c["ticket_id"])
    faults = Faults([*(task.faults if task else []), *(c.get("extra_faults") or [])])
    for tool, mode in c.get("faults_seen") or []:
        if faults.left.get((tool, mode), 0) > 0:
            faults.left[(tool, mode)] -= 1
    return World(PRACTICE_DB, c["ticket_id"], faults)


def log(**fields) -> None:
    print(json.dumps({"server": SERVER_NAME, **fields}), file=sys.stderr, flush=True)


def _read(name: str, arguments: dict, ctx: Context) -> str:
    c = context(ctx)
    w = world_for(c)
    r = run_read(name, arguments, c["customer_id"], w)
    log(event="tool_call", tool=name, ok=r.ok, code=r.code, ticket=c["ticket_id"])
    return json.dumps({"ok": r.ok, "data": r.data, "error": r.error, "code": r.code, "order_ids": r.order_ids,
                       "faults": [list(f) for f in w.faults.seen]}, ensure_ascii=False)


def _write(tool: str, ctx: Context, call) -> str:
    c = context(ctx)
    w = world_for(c)
    try:
        result = call(w, c)
        out = {"ok": True, "result": result}
    except ServiceError as e:
        out = {"ok": False, "error_kind": e.code, "error": str(e)}
    log(event="write", tool=tool, ok=out["ok"], ticket=c["ticket_id"], kind=out.get("error_kind"))
    out["faults"] = [list(f) for f in w.faults.seen]
    return json.dumps(out, ensure_ascii=False)


def _owner_check(w: World, c: dict, order_id: str) -> None:
    if w.owner(order_id) != c["customer_id"]:
        from resolver.systems import PermissionDenied

        raise PermissionDenied(f"{order_id} is not an order of this customer")


def build_server() -> MCPServer:
    mcp = MCPServer(SERVER_NAME, version=__version__,
                    instructions="Larkfield's practice order systems. Every write needs an operation ID.")

    @mcp.tool()
    def get_order(order_id: str, ctx: Context) -> str:
        """Look up one of this customer's orders by its order ID."""
        return _read("get_order", {"order_id": order_id}, ctx)

    @mcp.tool()
    def get_customer_orders(ctx: Context) -> str:
        """List this customer's orders."""
        return _read("get_customer_orders", {}, ctx)

    @mcp.tool()
    def get_payments(order_id: str, ctx: Context) -> str:
        """The payments and refunds of one of this customer's orders."""
        return _read("get_payments", {"order_id": order_id}, ctx)

    @mcp.tool()
    def search_policy(query: str, ctx: Context) -> str:
        """Search Larkfield's policy documents (3 best passages)."""
        return _read("search_policy", {"query": query}, ctx)

    @mcp.tool()
    def get_operation(operation_id: str, ctx: Context) -> str:
        """Whether a write with this operation ID happened, and its result (for reconciliation)."""
        c = context(ctx)
        found = world_for(c).operation(operation_id)
        return json.dumps({"ok": True, "result": found})

    @mcp.tool()
    def create_return_label(operation_id: str, order_id: str, sku: str, reason: str, ctx: Context) -> str:
        """Create a return label for one item of an order."""
        def call(w, c):
            _owner_check(w, c, order_id)
            return w.create_return_label(operation_id, order_id, sku, reason)
        return _write("create_return_label", ctx, call)

    @mcp.tool()
    def reship_item(operation_id: str, order_id: str, sku: str, quantity: int, ctx: Context) -> str:
        """Ship an item of an order again."""
        def call(w, c):
            _owner_check(w, c, order_id)
            return w.reship_item(operation_id, order_id, sku, quantity)
        return _write("reship_item", ctx, call)

    @mcp.tool()
    def request_refund(operation_id: str, order_id: str, amount: float, reason_code: str, ctx: Context,
                       payment_id: str = "") -> str:
        """Refund an amount of an order (a mock: no money moves)."""
        def call(w, c):
            _owner_check(w, c, order_id)
            return w.request_refund(operation_id, order_id, amount, reason_code, payment_id or None)
        return _write("request_refund", ctx, call)

    @mcp.tool()
    def add_ticket_note(operation_id: str, note: str, ctx: Context) -> str:
        """Add a note to the ticket."""
        return _write("add_ticket_note", ctx, lambda w, c: w.add_ticket_note(operation_id, note))

    return mcp
