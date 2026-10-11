"""Sign-in: tokens are checked, sessions are signed, and a cookie request needs the CSRF header."""

import time

import pytest

from doc_assistant.login import SESSION_COOKIE, sign, unsign


@pytest.mark.parametrize("make, code", [
    (lambda t: "not-a-token", "malformed"),
    (lambda t: t[:-4] + "AAAA", "bad_signature"),
    (lambda t: t, None),
])
def test_bearer_tokens_are_checked(client, token, make, code):
    good = token("usr-sam")["Authorization"][7:]
    r = client.get("/v1/me", headers={"Authorization": f"Bearer {make(good)}"})
    if code is None:
        assert r.status_code == 200 and r.json()["user"]["user_id"] == "usr-sam"
    else:
        assert r.status_code == 401 and code in r.json()["message"]


def test_an_expired_or_foreign_token_is_refused(client, token):
    old = token("usr-sam", exp=int(time.time()) - 3600)
    assert "expired" in client.get("/v1/me", headers=old).json()["message"]
    other = token("usr-sam", aud="another-api")
    assert "wrong_audience" in client.get("/v1/me", headers=other).json()["message"]


def test_a_session_cookie_is_signed_and_expires():
    s = sign({"sub": "usr-sam", "exp": time.time() + 60}, "secret")
    assert unsign(s, "secret")["sub"] == "usr-sam"
    assert unsign(s, "another-secret") is None
    body, mac = s.split(".")
    assert unsign(body.replace(body[5], "A" if body[5] != "A" else "B", 1) + "." + mac, "secret") is None
    assert unsign(sign({"sub": "usr-sam", "exp": time.time() - 1}, "secret"), "secret") is None


def test_a_cookie_request_that_changes_something_needs_the_csrf_header(client):
    cookie = sign({"sub": "usr-sam", "name": "Sam", "csrf": "the-csrf", "exp": time.time() + 60}, "test-session-secret")
    client.cookies.set(SESSION_COOKIE, cookie)
    assert client.get("/v1/tenants/larkfield/documents").status_code == 200
    r = client.post("/v1/tenants/larkfield/answers", json={"question": "Hello?"})
    assert r.status_code == 403 and r.json()["code"] == "csrf_failed"
    r = client.post("/v1/tenants/larkfield/answers", json={"question": "Hello?"}, headers={"X-CSRF-Token": "the-csrf"})
    assert r.status_code == 200
    assert client.get("/auth/session").json()["csrf_token"] == "the-csrf"


def test_login_redirects_only_to_a_local_path(client, monkeypatch):
    monkeypatch.setattr(client.app.state.validator.provider, "discovery",
                        lambda: {"authorization_endpoint": "http://localhost:8400/authorize"})
    r = client.get("/auth/login?return_to=https://evil.example/", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"].startswith("http://localhost:8400/authorize?")
    assert "code_challenge_method=S256" in r.headers["location"]
    assert unsign(r.cookies["assistant_login"], "test-session-secret")["return_to"] == "/app/"
