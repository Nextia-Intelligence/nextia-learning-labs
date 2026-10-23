"""Langfuse: the same Collector with a second trace destination; every span carries the run as session.id."""

from pathlib import Path

from obs.model import Telemetry
from resolver.__main__ import main

COLLECTOR = Path(__file__).resolve().parent.parent / "collector"


def test_the_langfuse_configuration():
    text = (COLLECTOR / "otelcol-config-langfuse.yaml").read_text()
    assert "${env:LANGFUSE_BASE_URL}/api/public/otel" in text and "basicauth/langfuse" in text
    assert "exporters: [otlp_http/langfuse]" in text and "LANGFUSE_SECRET_KEY}" in text
    assert "sk-lf-" not in text and "pk-lf-" not in text            # no key in the file


def test_session_id_is_the_run(telemetry_files, capsys):
    main(["run", "T-80008", "--variant", "agent", "--model", "chat-small"])
    telemetry_files.flush()
    run = next(iter(Telemetry(telemetry_files.folder).runs.values()))
    assert {s.get("session.id") for s in run.spans} == {run.run_id}
