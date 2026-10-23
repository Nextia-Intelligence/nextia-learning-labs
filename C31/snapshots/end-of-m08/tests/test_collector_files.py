"""The Collector's configuration: redaction, sampling for traces only, and the audit route."""

from pathlib import Path

COLLECTOR = Path(__file__).resolve().parent.parent / "collector"


def test_redaction_sampling_and_routing_are_in_the_configuration():
    text = (COLLECTOR / "otelcol-config.yaml").read_text()
    assert 'delete_key(attributes, "gen_ai.input.messages")' in text
    assert "tail_sampling:" in text and "processors: [memory_limiter, transform/redact, tail_sampling, batch]" in text
    logs = text.split("    logs:")[1]
    assert "tail_sampling" not in logs                    # never for events and audit events
    assert 'condition: attributes["audit.type"] != nil' in text


def test_the_standalone_configuration_writes_files():
    text = (COLLECTOR / "standalone.yaml").read_text()
    assert "${env:OUT_DIR}/traces.jsonl" in text and "file/traces" in text
