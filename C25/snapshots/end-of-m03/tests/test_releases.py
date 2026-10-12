"""Release manifests and lineage (the MLOps course, Module 2)."""

import json
import tomllib
from dataclasses import replace

import pytest
from conftest import TEST_SETTINGS
from test_jobs import TICKET, run_worker

from ops.__main__ import main
from ticket_api import config, releases


def write_release(folder, prompt="assistant-v2", **options) -> dict:
    manifest = releases.build(prompt, commit="test", **options)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{manifest['id']}.toml").write_text(releases.to_toml(manifest), encoding="utf-8")
    return manifest


def test_a_manifest_names_every_version_and_its_id_follows_its_content():
    m = releases.build("assistant-v2", commit="abc")
    assert m["id"].startswith("1.5.0-") and len(m["id"]) == 12
    assert m["assistant"]["prompt_fingerprint"] == releases.assistant.fingerprint("assistant-v2")
    assert m["data"]["evaluation_set"] == "d4c96eaa10c0"
    assert m["model"]["expected_version"] == "gpt-6-luna-2026-09-22"
    assert m["database"]["last_migration"] == releases.migrations()[-1]
    assert releases.build("assistant-v2", commit="abc")["id"] == m["id"]  # reproducible
    assert releases.build("assistant-v3", commit="abc")["id"] != m["id"]
    assert tomllib.loads(releases.to_toml(m)) == m  # the TOML file reads back the same


def test_the_service_takes_its_prompt_from_the_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "FOLDER", tmp_path)
    m = write_release(tmp_path, "assistant-v3")
    settings = config.with_release(replace(TEST_SETTINGS, release_id=m["id"]))
    assert settings.assistant_prompt == "assistant-v3"
    with pytest.raises(config.SettingsError, match="no release manifest"):
        config.with_release(replace(TEST_SETTINGS, release_id="1.5.0-000000"))


def test_a_manifest_that_does_not_match_the_files_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "FOLDER", tmp_path)
    m = write_release(tmp_path)
    path = tmp_path / f"{m['id']}.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(m["assistant"]["prompt_fingerprint"], "000000000000"), encoding="utf-8"
    )
    with pytest.raises(config.SettingsError, match="does not match"):
        config.with_release(replace(TEST_SETTINGS, release_id=m["id"]))


def test_every_ai_result_has_the_release_id(api, db_url, conn, tmp_path, monkeypatch):
    monkeypatch.setattr(releases, "FOLDER", tmp_path)
    m = write_release(tmp_path)
    r = api.post("/v1/tickets", json=TICKET).json()
    run_worker(db_url, release_id=m["id"])
    rows = conn.execute(
        "SELECT task, release_id FROM ai_runs WHERE ticket_id = %s ORDER BY run_id",
        (r["ticket_id"],),
    ).fetchall()
    assert rows == [
        {"task": "triage", "release_id": m["id"]},
        {"task": "embed", "release_id": m["id"]},
    ]


def test_diff_shows_what_changed_between_two_releases(tmp_path, capsys):
    v2, v3 = write_release(tmp_path), write_release(tmp_path, "assistant-v3")
    assert main(["release", "diff", v2["id"], v3["id"], "--releases", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "assistant.prompt" in out and "assistant-v3" in out
    assert "model.expected_version" not in out  # the same model in both


def test_verify_finds_a_changed_prompt(tmp_path, capsys):
    m = write_release(tmp_path)
    assert main(["release", "verify", m["id"], "--releases", str(tmp_path)]) == 0
    path = tmp_path / f"{m['id']}.toml"
    path.write_text(path.read_text().replace(m["code"]["fingerprint"], "x" * 12))
    assert main(["release", "verify", m["id"], "--releases", str(tmp_path)]) == 1
    assert "a file changed after the release" in capsys.readouterr().out


def test_trace_goes_from_a_ticket_to_its_versions(tmp_path, capsys):
    m = write_release(tmp_path / "releases")
    practice = json.loads(open("data/practice/tickets.jsonl").readline())
    from ops.cmd_trace import message_fingerprint

    records = [
        {
            "signal": "log",
            "time": 100.0,
            "event": "ticket.received",
            "attributes": {
                "ticket.id": "T-500001",
                "request.id": "r1",
                "ticket.channel": "web_form",
                "ticket.message_chars": 70,
                "ticket.language_guess": "en",
                "ticket.message_sha256": message_fingerprint(practice["message"]),
            },
        },
        {
            "signal": "log",
            "time": 104.0,
            "event": "ticket.triaged",
            "trace_id": "ab" * 16,
            "attributes": {
                "ticket.id": "T-500001",
                "outcome": "ok",
                "time_to_draft_s": 4.0,
                "team": "delivery",
                "needs_human": False,
                "release.id": m["id"],
                "prompt.version": "assistant-v2",
                "cost_usd": 0.0003,
                "gen_ai.response.model": "gpt-6-luna-2026-09-22",
                "gen_ai.response.finish_reasons": "stop",
                "evidence": "replayed",
                "gen_ai.usage.input_tokens": 1902,
                "gen_ai.usage.output_tokens": 262,
            },
        },
    ]
    path = tmp_path / "t.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records))
    assert main(["trace", "T-500001", str(path), "--releases", str(tmp_path / "releases")]) == 0
    out = capsys.readouterr().out
    assert f"practice ticket {practice['case_id']}" in out
    assert m["assistant"]["prompt_fingerprint"] in out and "d4c96eaa10c0" in out
    assert "WARNING" not in out


def test_the_experiment_record_of_prompt_v3(capsys):
    assert main(["experiments"]) == 0
    assert "EXP-001" in capsys.readouterr().out
    assert main(["experiments", "EXP-001"]) == 0
    out = capsys.readouterr().out
    assert "do not ship" in out and "T-65663" in out
