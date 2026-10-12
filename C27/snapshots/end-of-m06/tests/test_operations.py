"""Operations: usage limits, readiness, logs without content, and the release files."""

import json
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_the_daily_limit_stops_questions(make_client, token):
    client = make_client(daily_question_limit=2)
    h = token("usr-ines")
    codes = [client.post("/v1/tenants/bramble/answers", json={"question": "Gift cards?"}, headers=h).status_code
             for _ in range(3)]
    assert codes == [200, 200, 429]
    r = client.post("/v1/tenants/bramble/answers", json={"question": "Gift cards?"}, headers=h)
    assert r.json()["code"] == "limit_reached" and r.headers["retry-after"] == "3600"
    other = client.post("/v1/tenants/larkfield/answers", json={"question": "Gift cards?"}, headers=token("usr-sam"))
    assert other.status_code == 200   # the limit is per shop
    usage = client.get("/v1/tenants/bramble/usage", headers=h).json()
    assert usage["questions_today"] == 2 and usage["daily_question_limit"] == 2


def test_the_request_log_has_ids_but_no_content(client, token, caplog):
    with caplog.at_level(logging.INFO, logger="doc_assistant.access"):
        client.post("/v1/tenants/bramble/answers", json={"question": "A secret question?"}, headers=token("usr-ines"))
    line = json.loads(caplog.records[-1].message)
    assert line["status"] == 200 and line["tenant"] == "bramble" and line["user"] == "usr-ines" and line["request_id"]
    assert "secret" not in caplog.text and "Bearer" not in caplog.text


def test_ready_reports_a_missing_migration(client):
    with client.app.state.db.admin() as conn:
        conn.execute("DELETE FROM schema_migrations WHERE version = '005_usage_limits'")
    try:
        r = client.get("/ready")
        assert r.status_code == 503 and "005_usage_limits" in r.json()["message"]
    finally:
        with client.app.state.db.admin() as conn:
            conn.execute("INSERT INTO schema_migrations (version, checksum) SELECT '005_usage_limits', %s",
                         (__import__("doc_assistant.migrate", fromlist=["x"]).checksum(
                             ROOT / "migrations" / "005_usage_limits.sql"),))


def test_the_release_files_agree():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "compose.yaml").read_text()
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "USER app" in dockerfile and "HF_HUB_OFFLINE=1" in dockerfile
    assert "pgvector/pgvector:0.8.7-pg18-trixie" in compose and "pgvector/pgvector:0.8.7-pg18-trixie" in ci
    for step in ("ruff check", "scripts.holdout check", "python -m pytest", "scripts.isolation", "scripts.smoke"):
        assert step in ci.replace("scripts/smoke.py", "scripts.smoke")
    assert ".env" in (ROOT / ".dockerignore").read_text() and ".idp" in (ROOT / ".dockerignore").read_text()
