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
    chats = run.model_spans
    assert len(chats) == 2 and all(s.name == "chat chat-small" and s.kind == "client" for s in chats)
    first = chats[0]
    assert first.get(c.PROVIDER) == "azure.ai.openai" and first.get(c.INPUT_TOKENS) > 0
    assert first.get(c.PROMPT_NAME) == "agent" and len(first.get(c.PROMPT_VERSION)) == 8
    assert first.get(c.REPLAYED) == "exact"
    # the span lasts as long as the recorded call did
    assert abs(first.seconds - first.get(c.RECORDED_LATENCY)) < 0.01
    tools = run.tool_spans
    assert [s.tool for s in tools][:1] == ["get_order"] and tools[0].get(c.ARGS_SHAPE) == "order_id"


def test_no_text_leaves_the_application_by_default(telemetry_files, capsys):
    main(["run", "T-90103", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    problems, counted = check_folder(telemetry_files.folder)
    assert counted["spans"] > 3 and problems == []


def test_metrics_carry_tokens_and_runs(telemetry_files, capsys):
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    text = (telemetry_files.folder / "metrics.jsonl").read_text()
    names = [c.M_RUNS, c.M_AGENT_DURATION]
    names += [c.M_INPUT_TOKENS, c.M_INFERENCE_DURATION, c.M_TOOL_CALLS]
    names += [c.M_RUN_COST]
    for name in names:
        assert f'"name":"{name}"' in text, name
