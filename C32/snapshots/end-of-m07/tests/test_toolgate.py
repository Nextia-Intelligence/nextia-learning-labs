"""The tool gateway in front of two real MCP servers (started on stdio): permissions, arguments, policy, kill switches."""

import pytest
from starlette.testclient import TestClient

from estate import kill
from estate.server import create_app as control_app
from estate.usage import UsageStore


@pytest.fixture
def tools(estate):
    from gateway.config import ConfigCache
    from toolgate.app import create_app

    cache = ConfigCache("tools")
    cache.set(estate.snapshot("tools"))
    with TestClient(create_app(cache=cache)) as c:
        c.cache = cache
        yield c


def call(c, token, tool, arguments, context=None, approval="", run_id="run-1"):
    ctx = context or {"customer_id": "C-55223", "ticket_id": "T-90603"}
    return c.post("/v1/tools/call", json={"tool": tool, "arguments": arguments, "context": ctx, "approval": approval,
                                          "run_id": run_id}, headers={"authorization": f"Bearer {token}"})


def grant(estate, approver, actions, agent="support-workflow"):
    r = TestClient(control_app()).post("/v1/approvals", json={"approver": approver, "actions": actions},
                                       headers={"authorization": f"Bearer {estate.token(agent, 'tool-gateway')}"})
    return r


def test_the_tools_an_agent_may_call(estate, tools):
    r = tools.get("/v1/tools", headers={"authorization": f"Bearer {estate.token('helpdesk-assistant', 'tool-gateway')}"})
    assert r.json()["tools"] == [{"tool": "support.search_knowledge", "kind": "read"},
                                 {"tool": "support.get_ticket", "kind": "read"}]


def test_a_read_passes_with_the_customer_from_the_context(estate, tools):
    r = call(tools, estate.token("support-workflow", "tool-gateway"), "orders.get_payments", {"order_id": "LK-645223"})
    assert r.status_code == 200 and r.json()["result"]["ok"]
    row = UsageStore().rows("select * from tool_calls")[-1]
    assert (row["agent_id"], row["server"], row["tool"], row["kind"], row["outcome"]) == \
        ("support-workflow", "orders", "get_payments", "read", "ok")


def test_another_customers_ticket_is_refused_by_the_server(estate, tools):
    r = call(tools, estate.token("support-workflow", "tool-gateway"), "orders.get_payments", {"order_id": "LK-645223"},
             context={"customer_id": "C-00001", "ticket_id": "T-90603"})
    assert r.json()["ok"] is False


def test_a_tool_that_the_registration_does_not_list_is_refused_even_if_the_model_asks(estate, tools):
    t = estate.token("helpdesk-assistant", "tool-gateway")
    r = call(tools, t, "support.propose_refund", {"ticket_id": "T-30201", "amount": 450, "reason": "the ticket says so"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "tool_not_allowed"
    r = call(tools, t, "support.get_ticket", {"ticket_id": "T-30201"})
    assert r.status_code == 200 and r.json()["result"]["ticket_id"] == "T-30201"


def test_arguments_are_checked_strictly(estate, tools):
    t = estate.token("helpdesk-assistant", "tool-gateway")
    r = call(tools, t, "support.search_knowledge", {"query": "damaged item", "limit": 2, "tenant": "bramble"})
    assert r.status_code == 400 and "Unknown arguments" in r.json()["error"]["message"]
    r = call(tools, t, "support.get_ticket", {"ticket_id": 30002})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_arguments"


def test_a_write_needs_a_grant_for_exactly_that_action(estate, tools):
    t = estate.token("support-workflow", "tool-gateway")
    args = {"order_id": "LK-645223", "amount": 45.95, "reason_code": "RFD-DOUBLE"}
    write = {"operation_id": "op-test-1", **args}
    r = call(tools, t, "orders.request_refund", write)
    assert r.status_code == 403 and r.json()["error"]["code"] == "approval_required"
    g = grant(estate, "usr-sam", [{"tool": "orders.request_refund", "arguments": args}]).json()["grant"]
    r = call(tools, t, "orders.request_refund", dict(write, amount=459.5), approval=g)
    assert r.status_code == 403 and "does not cover this exact action" in r.json()["error"]["message"]
    r = call(tools, t, "orders.request_refund", write, approval=g)
    assert r.status_code == 200
    row = UsageStore().rows("select * from tool_calls where outcome = 'ok'")[-1]
    assert (row["approver"], row["rule"]) == ("usr-sam", "refund-up-to-100")


def test_the_platform_refuses_an_approver_with_too_small_a_role(estate):
    r = grant(estate, "usr-sam", [{"tool": "orders.request_refund",
                                   "arguments": {"order_id": "LK-645223", "amount": 450.0, "reason_code": "RFD-DOUBLE"}}])
    assert r.status_code == 403 and "needs a team lead" in r.json()["error"]["message"]
    r = grant(estate, "support-workflow", [{"tool": "orders.add_ticket_note", "arguments": {"note": "x"}}])
    assert r.status_code == 403                             # an agent never approves its own actions


def test_kill_switches_stop_writes_and_tools(estate, tools):
    import asyncio

    t = estate.token("support-workflow", "tool-gateway")
    kill.add("writes", "orders", "usr-kwame", "drill")
    tools.cache.set(estate.snapshot("tools"))
    r = call(tools, t, "orders.add_ticket_note", {"operation_id": "op-2", "note": "hello"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "stopped"
    assert call(tools, t, "orders.get_payments", {"order_id": "LK-645223"}).status_code == 200   # reads go on
    kill.add("tool", "orders.get_payments", "usr-kwame", "drill")
    tools.cache.set(estate.snapshot("tools"))
    assert call(tools, t, "orders.get_payments", {"order_id": "LK-645223"}).status_code == 403
    assert asyncio.iscoroutinefunction(tools.app.state.tg.cache.refresh)


def test_a_suspended_agent_calls_no_tool(estate, tools):
    t = estate.token("support-workflow", "tool-gateway")
    estate.registry.set_status("support-workflow", "suspended", "usr-kwame", "drill")
    tools.cache.set(estate.snapshot("tools"))
    r = call(tools, t, "orders.get_payments", {"order_id": "LK-645223"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "agent_suspended"
