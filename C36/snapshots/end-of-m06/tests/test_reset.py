from pathlib import Path

from larkroute.cli import main
from larkroute.commands import reset

ROOT = Path(__file__).resolve().parents[1]


def test_the_defaults_are_the_course_configuration():
    for f in (ROOT / "larkroute" / "defaults").glob("*.json"):
        assert (ROOT / "config" / f.name).read_bytes() == f.read_bytes(), f.name


def test_reset_puts_back_a_changed_rule_file(capsys, monkeypatch):
    monkeypatch.setattr(reset, "OUTPUTS", [])  # the test keeps your models and queues
    rules = ROOT / "config" / "rules.json"
    before = rules.read_bytes()
    rules.write_text("{}")
    try:
        main(["reset"])
    finally:
        out = capsys.readouterr().out
        if rules.read_bytes() != before:
            rules.write_bytes(before)
    assert "rules.json" in out and "all files are right" in out
