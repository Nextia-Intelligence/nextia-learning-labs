"""Tests of the practice app's tools for testers (learners never need to run these)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HELPDESK_HOME", str(tmp_path / "home"))
    from helpdesk import store
    store.reset()
    return tmp_path


def ask(text, seed=1, customer=None):
    from helpdesk import assistant
    cid = assistant.start(customer, seed, "sim")
    return cid, assistant.send(cid, text)


def test_versions_and_first_answer():
    import helpdesk
    assert helpdesk.APP_VERSION == "2.3.0" and helpdesk.MODEL_NAME == "sim-1"
    cid, out = ask("Do gift cards expire?")
    assert cid == "c-0001" and out["trace_id"] == "tr-0001-1"
    assert "never expire" in out["reply"]


def test_same_seed_same_answer_and_seeds_vary():
    replies = {ask("How long does a refund take to reach my card?", seed=s)[1]["reply"] for s in range(1, 13)}
    assert len(replies) > 3
    assert ask("Do gift cards expire?", seed=7)[1]["reply"] == ask("Do gift cards expire?", seed=7)[1]["reply"]


def test_trace_has_the_evidence():
    from helpdesk import store
    _, out = ask("How many days do I have to return an unused item?")
    t = store.get_trace(out["trace_id"])
    for key in ("app_version", "prompt_version", "model", "settings", "retrieved", "tool_calls", "cited", "output"):
        assert key in t
    assert t["settings"]["seed"] == 1 and t["retrieved"]


def test_export_and_replay(home, capsys):
    from helpdesk import __main__ as cli
    from helpdesk import export
    cid, _ = ask("Where is my order LK-200103?", seed=11)
    data = export.export(cid)
    assert data["app_version"] == "2.3.0" and data["seed"] == 11 and data["messages"][0]["role"] == "user"
    f = home / "conv.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    cli.main(["replay", str(f)])
    assert "1 of 1 replies are the same" in capsys.readouterr().out


def test_confirmation_flow_and_reset():
    from helpdesk import assistant, store
    cid = assistant.start("C-1001", 3, "sim")
    assert "Reply yes" in assistant.send(cid, "Please cancel order LK-200101.")["reply"]
    assert store.get_order("LK-200101")["status"] == "Processing"
    assert "cancelled" in assistant.send(cid, "yes")["reply"]
    assert store.get_order("LK-200101")["status"] == "Cancelled"
    store.reset()
    assert store.get_order("LK-200101")["status"] == "Processing"


def test_cli_version():
    out = subprocess.run([sys.executable, "-m", "helpdesk", "version"], cwd=ROOT, capture_output=True, text=True,
                         env={**os.environ}, check=True).stdout
    assert out.startswith("larkfield-helpdesk 2.3.0 | model sim-1")


def test_runner_on_example_cases(tmp_path):
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "c.yaml").write_text(
        "id: gift-cards\nmessage: Do gift cards expire?\nchecks:\n  - contains: never expire\n  - cites: gift-cards\n"
        "---\nid: impossible\nmessage: Do gift cards expire?\nchecks:\n  - contains: always expire\n",
        encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "qa", "run", str(cases), "--runs", "3", "--report-dir",
                        str(tmp_path / "rep")], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 1, r.stderr
    assert "PASS    gift-cards  3/3 passed" in r.stdout
    assert "FAIL    impossible  0/3 passed" in r.stdout
    assert list((tmp_path / "rep").glob("qa-*/report.md"))


def test_runner_rejects_a_bad_case(tmp_path):
    (tmp_path / "bad.yaml").write_text("id: x\nmessage: hi\nchecks:\n  - contain: hello\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "qa", "check", str(tmp_path)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 2 and "unknown check 'contain'" in r.stderr


def test_policy_pages_exist_for_every_section():
    from helpdesk import corpus
    docs = {(s.doc_id, s.version) for s in corpus.sections()}
    assert len({d for d, _ in docs}) == 19 and len(docs) == 20


def test_runner_rejects_a_quoted_boolean(tmp_path):
    (tmp_path / "q.yaml").write_text('id: x\nmessage: hi\nchecks:\n  - refuses: "false"\n', encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "qa", "check", str(tmp_path)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 2 and 'refuses must be true or false, not the text "false"' in r.stderr
