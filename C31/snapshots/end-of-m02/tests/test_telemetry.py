"""One run is one trace: the agent span, its model calls and tool calls, with the pinned GenAI names and no text."""

from obs.model import Telemetry
from obs.redaction import check_folder
from resolver import conventions as c
from resolver.__main__ import main


def spans_of(t):
    t.flush()
    return Telemetry(t.folder)


def test_a_run_is_one_trace_with_genai_spans(telemetry_files, capsys):
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    saved = spans_of(telemetry_files)
    run = next(iter(saved.runs.values()))
    assert len(run.trace_ids) == 1
    root = run.root
    assert root.name == "invoke_agent support-resolver" and root.get(c.OPERATION) == "invoke_agent"
    assert root.get(c.AGENT_ID) == "support-workflow" and root.get(c.PROPOSED) == "reply_only"
    assert root.get(c.TICKET_ID) == "T-80008" and run.outcome == "resolved"


def test_no_text_leaves_the_application_by_default(telemetry_files, capsys):
    main(["run", "T-90103", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    problems, counted = check_folder(telemetry_files.folder)
    assert counted["spans"] == 1 and problems == []


def test_metrics_carry_tokens_and_runs(telemetry_files, capsys):
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    text = (telemetry_files.folder / "metrics.jsonl").read_text()
    names = [c.M_RUNS, c.M_AGENT_DURATION]
    for name in names:
        assert f'"name":"{name}"' in text, name
