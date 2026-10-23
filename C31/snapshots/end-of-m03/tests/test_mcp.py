"""Optional (requirements-mcp.txt): the order lookup through an MCP server joins the same trace."""

import pytest

pytest.importorskip("mcp")

from obs.model import Telemetry  # noqa: E402
from resolver.__main__ import main  # noqa: E402


def test_the_mcp_call_is_in_the_same_trace(telemetry_files, capsys, monkeypatch):
    monkeypatch.setenv("RESOLVER_TOOLS", "mcp")
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    run = next(iter(Telemetry(telemetry_files.folder).runs.values()))
    names = [s.name for s in run.spans]
    assert "MCP send tools/call get_order" in names and "tools/call get_order" in names
    server = next(s for s in run.spans if s.name == "tools/call get_order")
    assert server.kind == "server" and len(run.trace_ids) == 1
