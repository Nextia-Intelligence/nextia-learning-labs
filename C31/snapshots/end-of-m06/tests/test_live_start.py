"""The live workflow: the reply is sent, the ticket is closed, and one log line says so (Amira's log)."""

from resolver import live
from resolver.__main__ import main


def test_a_reply_is_sent_and_logged(capsys, monkeypatch, tmp_path):
    log = tmp_path / "workflow.log"
    monkeypatch.setenv("RESOLVER_LOG", str(log))
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    out = capsys.readouterr().out
    assert "Reply sent. Ticket: resolved." in out
    line = log.read_text().strip()
    assert "ticket=T-80008" in line and "status=resolved" in line and "reply=sent" in line


def test_the_log_line_does_not_say_which_write_happened_twice(capsys, monkeypatch, tmp_path):
    log = tmp_path / "workflow.log"
    monkeypatch.setenv("RESOLVER_LOG", str(log))
    main(["reset"])
    main(["run", "T-90104", "--variant", "agent_structured", "--model", "chat-strong"])
    run_id = [x for x in capsys.readouterr().out.split() if x.startswith("T-90104-")][0]
    main(["approve", run_id, "--as", "agent", "--fault", "request_refund:timeout_after_write", "--naive-retry"])
    assert "status=resolved writes=1 reply=sent" in log.read_text()     # green, and one write
    from resolver.systems import PRACTICE_DB, World
    refunds = [c for c in World(PRACTICE_DB).changes() if c["tool"] == "request_refund"]
    assert len(refunds) == 2                                           # but two refunds were paid


def test_the_hard_ticket_rule():
    assert live.is_hard("My order LK-123456 hasn't arrived, it is late") and not live.is_hard("Please send a return label")
