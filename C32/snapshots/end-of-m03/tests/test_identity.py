"""One identity per agent: client credentials, short-lived signed tokens, and the checks on them."""

import time

import jwt
import pytest

from estate import identity, registry
from conftest import PROJECT


@pytest.fixture
def triage():
    registry.register(registry.read_form(PROJECT / "registrations" / "ticket-triage.yaml"), "usr-kwame")
    return identity.issue_credentials("ticket-triage", "usr-kwame")


def test_a_token_has_the_shape_of_the_earlier_courses(triage):
    t = identity.token(*triage, "model-gateway")["access_token"]
    head = jwt.get_unverified_header(t)
    claims = jwt.decode(t, options={"verify_signature": False})
    assert head["alg"] == "RS256" and head["typ"] == "at+jwt"
    assert claims["sub"] == "ticket-triage" and claims["aud"] == "model-gateway" and claims["exp"] - claims["iat"] == 600
    assert not {"team", "role", "tenant", "capabilities"} & set(claims)     # permissions come from the registry


def test_the_secret_is_stored_only_as_a_hash(triage):
    from contextlib import closing

    with closing(registry.db()) as con:
        row = con.execute("select secret_hash from credentials").fetchone()
    assert triage[1] not in row[0] and len(row[0]) == 64


def test_the_verifier_checks_signature_audience_and_time(triage):
    t = identity.token(*triage, "model-gateway")["access_token"]
    v = identity.Verifier(identity.jwks())
    assert v.verify(t, "model-gateway")["sub"] == "ticket-triage"
    with pytest.raises(identity.TokenError) as e:
        v.verify(t, "tool-gateway")
    assert e.value.code == "wrong_audience"
    with pytest.raises(identity.TokenError) as e:
        v.verify(t, "model-gateway", now=time.time() + 3600)
    assert e.value.code == "expired_token"
    forged = jwt.encode(jwt.decode(t, options={"verify_signature": False}), "a-made-up-secret-of-thirty-two-bytes!", algorithm="HS256",
                        headers={"typ": "at+jwt", "kid": identity.kid()})
    with pytest.raises(identity.TokenError):
        v.verify(forged, "model-gateway")


def test_a_wrong_secret_or_a_suspended_agent_gets_no_token(triage):
    with pytest.raises(identity.TokenError):
        identity.token("ticket-triage", "wrong", "model-gateway")
    registry.set_status("ticket-triage", "suspended", "usr-kwame", "test")
    with pytest.raises(identity.TokenError) as e:
        identity.token(*triage, "model-gateway")
    assert "suspended" in str(e.value)


def test_revoked_credentials_get_no_token(triage):
    identity.revoke("ticket-triage", "usr-kwame", "leaked in a log")
    with pytest.raises(identity.TokenError):
        identity.token(*triage, "model-gateway")
    assert identity.revoked_before("ticket-triage") is not None


def agent_view(agent_id):
    live, revoked = identity.credential_ids(agent_id)
    return {"credentials": live, "revoked_credentials": revoked}


def claims_of(t):
    return jwt.decode(t, options={"verify_signature": False})


def test_each_secret_is_its_own_credential_and_the_token_names_it(triage):
    t = identity.token(*triage, "model-gateway")["access_token"]
    assert claims_of(t)["cid"] == "ticket-triage#1"
    assert identity.check_credential(agent_view("ticket-triage"), claims_of(t)) is None


def test_a_revoked_token_stays_refused_after_a_new_secret(triage):
    old = claims_of(identity.token(*triage, "model-gateway")["access_token"])
    identity.revoke("ticket-triage", "usr-kwame", "leaked in a log")
    _, secret = identity.issue_credentials("ticket-triage", "usr-kwame")       # before the old token expires
    new = claims_of(identity.token("ticket-triage", secret, "model-gateway")["access_token"])
    assert new["cid"] == "ticket-triage#2" and new["iat"] - old["iat"] <= 1   # the same second, or the next one
    assert identity.check_credential(agent_view("ticket-triage"), old)[0] == "token_revoked"
    assert identity.check_credential(agent_view("ticket-triage"), new) is None


def test_a_new_secret_replaces_the_old_one(triage):
    old_token = claims_of(identity.token(*triage, "model-gateway")["access_token"])
    identity.issue_credentials("ticket-triage", "usr-kwame")                  # no revoke first
    with pytest.raises(identity.TokenError):
        identity.token(*triage, "model-gateway")                              # the old secret
    assert identity.check_credential(agent_view("ticket-triage"), old_token)[0] == "token_revoked"
    assert registry.events("ticket-triage")[1]["action"] == "credentials_revoked"


def test_a_token_without_a_credential_id_is_refused(triage):
    claims = claims_of(identity.token(*triage, "model-gateway")["access_token"])
    del claims["cid"]
    forged = jwt.encode(claims, identity.signing_key(), algorithm="RS256",
                        headers={"kid": identity.kid(), "typ": "at+jwt"})
    with pytest.raises(identity.TokenError) as e:
        identity.Verifier(identity.jwks()).verify(forged, "model-gateway")
    assert e.value.code == "invalid_token"
