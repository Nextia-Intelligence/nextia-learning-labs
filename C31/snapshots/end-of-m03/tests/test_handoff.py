"""The two workers: the handoff message carries the trace context, or the run breaks into two traces."""

from obs.model import Telemetry
from resolver.__main__ import main


def test_context_travels_with_the_handoff(telemetry_files, capsys):
    main(["run", "T-90103", "--variant", "workers", "--model", "chat-small"])
    telemetry_files.flush()
    run = next(iter(Telemetry(telemetry_files.folder).runs.values()))
    names = [s.name for s in run.spans]
    assert "invoke_agent investigator" in names and "invoke_agent resolver" in names
    assert len(run.trace_ids) == 1
    resolver = next(s for s in run.spans if s.name == "invoke_agent resolver")
    assert resolver.get("larkfield.handoff.context") == "propagated" and resolver.get("larkfield.handoff.from") == "investigator"


def test_without_the_context_the_story_breaks(telemetry_files, capsys, monkeypatch):
    monkeypatch.setenv("OBS_HANDOFF_CONTEXT", "off")
    main(["run", "T-90103", "--variant", "workers", "--model", "chat-small"])
    telemetry_files.flush()
    spans = Telemetry(telemetry_files.folder).spans
    resolver = next(s for s in spans if s.name == "invoke_agent resolver")
    root = next(s for s in spans if s.name.startswith("invoke_workflow"))
    assert resolver.trace_id != root.trace_id and not resolver.parent_id
    assert resolver.get("larkfield.handoff.context") == "missing"
