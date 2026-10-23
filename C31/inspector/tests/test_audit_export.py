"""The audit export of the double refund (T-90104, run R-1014-040): the course's story, as a Markdown file."""

import os
import subprocess
import sys

import pytest
from conftest import ROOT, get, truth

import sync


def double_refund_run() -> str:
    runs = [r for r in truth("week")["runs"] if "double_refund" in r["scenarios"] and r["ticket"] == "T-90104"]
    return runs[0]["run_id"]


def test_markdown_export(server):
    run_id = double_refund_run()
    status, headers, body = get(f"{server}/api/runs/{run_id}/audit.md")
    assert status == 200
    assert headers["Content-Type"].startswith("text/markdown")
    assert f'filename="audit-T-90104-{run_id}.md"' in headers["Content-Disposition"]
    text = body.decode("utf-8")
    assert text.startswith("# Audit story: ticket T-90104\n")
    assert "(the trail verifies)" in text
    assert "| Time (Toronto) | What happened |" in text
    assert "proposed: resolve (rule W2): refund 9.95 (RFD-LATE) on LK-793996" in text
    assert "approved the proposal of record" in text
    assert ": TIMEOUT (attempt 1, key" in text and ": done (attempt 2, key" in text
    assert "refund 9.95 (RFD-LATE) on LK-793996: 2 call(s) that may have changed it (timeout, done), 2 different key(s)" in text


def test_export_is_the_course_tools_story(server):
    """The same text as `python -m obs audit story RUN --data data/telemetry/week --markdown` in the project."""
    project = sync.find_project()
    if project is None:
        pytest.skip("the course project is not beside the inspector")
    run_id = double_refund_run()
    cli = subprocess.run([sys.executable, "-m", "obs", "audit", "story", run_id, "--data", "data/telemetry/week",
                          "--markdown"], cwd=project, capture_output=True, text=True, check=True,
                         env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
    _, _, body = get(f"{server}/api/runs/{run_id}/audit.md")
    assert body.decode("utf-8") == cli.stdout


def test_no_export_for_an_unknown_run(server):
    status, _, _ = get(f"{server}/api/runs/R-0000-000/audit.md")
    assert status == 404


def test_root_is_importable():
    assert (ROOT / "larkfield_inspector" / "vendor" / "obs" / "story.py").exists()
